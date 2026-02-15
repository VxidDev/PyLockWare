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

        # Генерируем действительно случайные значения для состояний
        unique_states = set()
        shuffled_indices = []
        
        for i in range(len(blocks)):
            # Генерируем случайное значение до тех пор, пока не найдем уникальное
            while True:
                rand_state = random.randint(1000, 999999)  # Случайное число в диапазоне
                if rand_state not in unique_states:
                    unique_states.add(rand_state)
                    shuffled_indices.append(rand_state)
                    break
        
        # Создаем словарь соответствия: оригинальный индекс -> случайное состояние
        self.block_to_state_map = dict(zip(range(len(blocks)), shuffled_indices))

        # Также создаем обратный словарь: случайное состояние -> оригинальный индекс
        self.state_to_block_map = dict(zip(shuffled_indices, range(len(blocks))))

        # Генерируем случайное значение для финального состояния
        while True:
            final_rand_state = random.randint(1000, 999999)
            if final_rand_state not in unique_states:
                self.final_state = final_rand_state
                break

        # -----------------------------
        # Генерация state machine
        # -----------------------------

        new_body = []

        # __state = перемешанный индекс первого блока
        initial_state = self.block_to_state_map[0] if 0 in self.block_to_state_map else 0
        new_body.append(
            ast.Assign(
                targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                value=ast.Constant(initial_state),
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

        # Используем перемешанные индексы для генерации ветвлений
        for idx, block in enumerate(blocks):
            # Получаем перемешанный индекс для этого блока
            shuffled_state = self.block_to_state_map[idx]
            case_body = self._process_block(block, idx, len(blocks), ret_var, is_generator, shuffled_state)

            cases.append(
                ast.If(
                    test=ast.Compare(
                        left=ast.Name(id=self.state_var, ctx=ast.Load()),
                        ops=[ast.Eq()],
                        comparators=[ast.Constant(shuffled_state)],
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

    def _process_block(self, block, idx, total_blocks, ret_var, is_generator, current_shuffled_state=None):
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
                next_idx = idx + 1
                if next_idx < total_blocks:
                    next_shuffled_state = self.block_to_state_map[next_idx]
                    case_body.append(
                        ast.Assign(
                            targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                            value=ast.Constant(next_shuffled_state),
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

        # переход к следующему состоянию (только если в теле нет других переходов)
        has_explicit_transition = any(
            isinstance(s, ast.Assign) and 
            isinstance(s.targets[0], ast.Name) and 
            s.targets[0].id == self.state_var
            for s in case_body
        )
        
        if not has_explicit_transition:
            next_idx = idx + 1
            if next_idx < total_blocks:
                next_shuffled_state = self.block_to_state_map[next_idx]
                case_body.append(
                    ast.Assign(
                        targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                        value=ast.Constant(next_shuffled_state),
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
        next_idx = current_idx + 1
        if next_idx < total_blocks:
            next_shuffled_state = self.block_to_state_map[next_idx]
            state_value = ast.Constant(next_shuffled_state)
        else:
            state_value = ast.Constant(self.final_state)
            
        body.append(
            ast.Assign(
                targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                value=state_value,
            )
        )
        return body

    def _process_try(self, try_node, current_idx, total_blocks):
        """Преобразует try-except"""
        next_idx = current_idx + 1
        body = [try_node]
        if next_idx < total_blocks:
            next_shuffled_state = self.block_to_state_map[next_idx]
            state_value = ast.Constant(next_shuffled_state)
        else:
            state_value = ast.Constant(self.final_state)
            
        body.append(
            ast.Assign(
                targets=[ast.Name(id=self.state_var, ctx=ast.Store())],
                value=state_value,
            )
        )
        return body

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