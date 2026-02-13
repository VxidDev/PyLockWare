"""
State Machine Transformer for PyLockWare
Transforms functions into state machines to obfuscate control flow
"""
import ast
import random
import string
from pylockware.core.name_generator import generate_random_name


class StateMachineTransformer(ast.NodeTransformer):
    def __init__(self, name_gen_settings='english'):
        self.func_counter = 0
        self.state_var = None
        self.final_state = None
        self.name_gen_settings = name_gen_settings

    # -----------------------------
    # Utility
    # -----------------------------

    def _rand(self, prefix="_s"):
        # Generate a random name with the specified prefix (or default "_s_") and the character set settings
        if prefix:
            return generate_random_name(prefix + "_", self.name_gen_settings)
        else:
            # Generate a random name without a specific prefix but still with underscore
            return generate_random_name("_", self.name_gen_settings)

    def _contains_async(self, node):
        return any(isinstance(n, ast.AsyncFunctionDef) for n in ast.walk(node))

    # -----------------------------
    # Core
    # -----------------------------

    def visit_ClassDef(self, node):
        """Явно обрабатываем класс - обфусцируем все методы внутри"""
        new_body = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                # ПРАВИЛЬНО: используем self.visit, чтобы рекурсивно обработать вложенные узлы
                new_body.append(self.visit(item))
            elif isinstance(item, ast.ClassDef):
                # ПРАВИЛЬНО: рекурсивно обрабатываем вложенные классы
                new_body.append(self.visit(item))
            else:
                # Атрибуты, docstrings и т.д.
                new_body.append(self.generic_visit(item))
        node.body = new_body
        return node

    def visit_FunctionDef(self, node):
        # Пропускаем только async
        if self._contains_async(node):
            return self.generic_visit(node)

        # Минимальный размер
        if len(node.body) < 1:
            return self.generic_visit(node)

        self.func_counter += 1
        old_state = self.state_var
        # Use the name generator settings to create state and return variables without specific prefixes
        self.state_var = self._rand("")
        ret_var = self._rand("")

        is_generator = any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(node))

        # Разбиваем тело на блоки
        blocks = self._split_into_blocks(node.body)

        if len(blocks) <= 1 and not is_generator:
            self.state_var = old_state
            return self.generic_visit(node)

        self.final_state = len(blocks)

        # -----------------------------
        # Генерация state machine
        # -----------------------------

        new_body = []

        # __state = 0
        new_body.append(
            ast.Assign(
                targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                value=ast.Constant(0),
            )
        )

        # __ret = None
        if not is_generator:
            new_body.append(
                ast.Assign(
                    targets=[ast.Name(id=ret_var, ctx=ast.Store())],
                    value=ast.Constant(None),
                )
            )

        cases = []

        for idx, block in enumerate(blocks):
            case_body = self._process_block(block, idx, len(blocks), ret_var, is_generator)

            cases.append(
                ast.If(
                    test=ast.Compare(
                        left=ast.Name(id=self.state_var, ctx=ast.Load()),
                        ops=[ast.Eq()],
                        comparators=[ast.Constant(idx)],
                    ),
                    body=case_body,
                    orelse=[],
                )
            )

        # while state != FINAL
        loop = ast.While(
            test=ast.Compare(
                left=ast.Name(id=self.state_var, ctx=ast.Load()),
                ops=[ast.NotEq()],
                comparators=[ast.Constant(self.final_state)],
            ),
            body=cases,
            orelse=[],
        )

        new_body.append(loop)

        # return
        if is_generator:
            new_body.append(ast.Return(value=None))
        else:
            new_body.append(ast.Return(value=ast.Name(id=ret_var, ctx=ast.Load())))

        node.body = new_body

        # ВАЖНО: теперь НЕ вызываем generic_visit, т.к. мы полностью переписали тело
        # Но всё равно нужно рекурсивно обработать вложенные узлы (например, вложенные функции)
        # Это делает generic_visit для всей функции целиком, включая новое тело
        self.state_var = old_state
        return self.generic_visit(node)

    def _split_into_blocks(self, body):
        """Агрессивное разбиение на блоки"""
        blocks = []
        current_block = []

        for stmt in body:
            if isinstance(stmt, (ast.For, ast.While, ast.Try, ast.With, ast.Match,
                                 ast.If, ast.FunctionDef, ast.ClassDef)):
                if current_block:
                    blocks.append(current_block)
                    current_block = []
                blocks.append([stmt])
            elif isinstance(stmt, ast.Return):
                if current_block:
                    blocks.append(current_block)
                    current_block = []
                blocks.append([stmt])
            elif len(current_block) >= 2:
                blocks.append(current_block)
                current_block = [stmt]
            else:
                current_block.append(stmt)

        if current_block:
            blocks.append(current_block)

        return blocks

    def _process_block(self, block, idx, total_blocks, ret_var, is_generator):
        """Обрабатывает блок"""
        case_body = []

        for stmt in block:
            if isinstance(stmt, ast.Return):
                if is_generator:
                    if stmt.value:
                        case_body.append(ast.Expr(value=ast.Yield(value=stmt.value)))
                    case_body.append(ast.Return(value=None))
                else:
                    case_body.append(
                        ast.Assign(
                            targets=[ast.Name(id=ret_var, ctx=ast.Store())],
                            value=stmt.value if stmt.value else ast.Constant(None),
                        )
                    )
                    case_body.append(
                        ast.Assign(
                            targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                            value=ast.Constant(self.final_state),
                        )
                    )

            elif isinstance(stmt, (ast.Yield, ast.YieldFrom)):
                case_body.append(stmt)
                if idx < total_blocks - 1:
                    case_body.append(
                        ast.Assign(
                            targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                            value=ast.Constant(idx + 1),
                        )
                    )
                    case_body.append(ast.Return(value=None))

            elif isinstance(stmt, (ast.For, ast.While)):
                case_body.extend(self._process_loop(stmt, idx, total_blocks))

            elif isinstance(stmt, ast.Try):
                case_body.extend(self._process_try(stmt, idx, total_blocks))

            elif isinstance(stmt, (ast.FunctionDef, ast.ClassDef)):
                # Вложенные определения - рекурсивно обрабатываем
                if isinstance(stmt, ast.FunctionDef):
                    case_body.append(self.visit(stmt))
                else:
                    case_body.append(self.visit(stmt))

            else:
                case_body.append(stmt)

        # переход к следующему состоянию
        if not any(isinstance(s, (ast.Return, ast.Yield, ast.YieldFrom)) for s in case_body):
            if idx < total_blocks - 1:
                case_body.append(
                    ast.Assign(
                        targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                        value=ast.Constant(idx + 1),
                    )
                )
            else:
                case_body.append(
                    ast.Assign(
                        targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                        value=ast.Constant(self.final_state),
                    )
                )

        return case_body

    def _process_loop(self, loop_node, current_idx, total_blocks):
        """Преобразует цикл"""
        body = [loop_node]
        body.append(
            ast.Assign(
                targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                value=ast.Constant(current_idx + 1 if current_idx < total_blocks - 1 else self.final_state),
            )
        )
        return body

    def _process_try(self, try_node, current_idx, total_blocks):
        """Преобразует try-except"""
        return [try_node]

    def apply_transformation(self, code):
        """Apply state machine transformation to Python code."""
        try:
            tree = ast.parse(code)
            transformed_tree = self.visit(tree)
            ast.fix_missing_locations(transformed_tree)
            return ast.unparse(transformed_tree)
        except Exception as e:
            print(f"State machine transformation failed: {e}")
            return code