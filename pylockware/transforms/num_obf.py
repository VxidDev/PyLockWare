#!/usr/bin/env python3
import random
import ast
import operator


OPS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '//': operator.floordiv,
    '%': operator.mod,
    '^': operator.xor,
    '<<': operator.lshift,
    '>>': operator.rshift,
}


def atomic_expr(n: int) -> str:
    """
    Гарантированно возвращает выражение != литералу,
    которое вычисляется в n
    """
    if n == 0:
        return "(~(-1))"          # 0
    if n == 1:
        return "(2 >> 1)"         # 1
    if n == -1:
        return "(~0)"             # -1
    if n < 0:
        return f"(-{atomic_expr(-n)})"

    k = random.randint(1, 5)
    return f"(({n + k}) - {k})"


def build_expr(target: int, depth: int, max_depth: int) -> str:
    if depth >= max_depth:
        return atomic_expr(target)

    op = random.choice(list(OPS.keys()))

    if op == '+':
        a = random.randint(-50, 50)
        b = target - a
    elif op == '-':
        a = random.randint(-50, 50)
        b = a - target
    elif op == '*':
        if target == 0:
            a, b = random.randint(1, 5), 0
        else:
            a = random.choice([d for d in range(1, abs(target) + 1) if target % d == 0])
            b = target // a
    elif op == '//':
        b = random.randint(1, 5)
        a = target * b
    elif op == '%':
        b = random.randint(abs(target) + 1, abs(target) + 20)
        a = target
    elif op == '<<':
        b = random.randint(1, 3)
        a = target >> b
    elif op == '>>':
        b = random.randint(1, 3)
        a = target << b
    elif op == '^':
        a = random.randint(1, 100)
        b = target ^ a
    else:
        return atomic_expr(target)

    left = build_expr(a, depth + 1, max_depth)
    right = build_expr(b, depth + 1, max_depth)
    expr = f"({left} {op} {right})"

    # жёсткая проверка
    if eval(expr) != target:
        return atomic_expr(target)

    return expr


def obfuscate_number(n: int) -> str:
    expr = build_expr(n, 0, random.randint(2, 4))
    assert eval(expr) == n
    return expr


def obfuscate_float(n: float) -> str:
    """
    Обфусцирует float значение путем преобразования его в строку,
    а затем в выражение, которое воссоздает это значение.
    """
    s = str(n)
    # Преобразуем строку в список ASCII кодов
    ascii_codes = [ord(c) for c in s]
    
    # Создаем выражение, которое воссоздаст строку и преобразует её в float
    codes_str = ', '.join(map(str, ascii_codes))
    return f"float(''.join(chr(x) for x in [{codes_str}]))"


class NumberObfuscator(ast.NodeTransformer):
    """AST transformer to obfuscate integer and float literals in Python code."""

    def __init__(self):
        self.number_counter = 0

    def visit_Constant(self, node):
        """Handle numeric constants in newer Python versions."""

        if isinstance(node.value, int) and not isinstance(node.value, bool):
            # Obfuscate the number regardless of size
            obfuscated_expr = obfuscate_number(node.value)

            # Parse the obfuscated expression back to an AST node
            try:
                obfuscated_node = ast.parse(obfuscated_expr, mode='eval').body
                return obfuscated_node
            except:
                # If parsing fails, return the original node
                return node
        
        elif isinstance(node.value, float):
            # Obfuscate the float value
            obfuscated_expr = obfuscate_float(node.value)

            # Parse the obfuscated expression back to an AST node
            try:
                obfuscated_node = ast.parse(obfuscated_expr, mode='eval').body
                return obfuscated_node
            except:
                # If parsing fails, return the original node
                return node

        return node

    def visit_Num(self, node):
        """Handle numeric literals in older Python versions."""

        if isinstance(node.n, int):
            # Obfuscate the number regardless of size
            obfuscated_expr = obfuscate_number(node.n)

            # Parse the obfuscated expression back to an AST node
            try:
                obfuscated_node = ast.parse(obfuscated_expr, mode='eval').body
                return obfuscated_node
            except:
                # If parsing fails, return the original node
                return node
                
        elif isinstance(node.n, float):
            # Obfuscate the float value
            obfuscated_expr = obfuscate_float(node.n)

            # Parse the obfuscated expression back to an AST node
            try:
                obfuscated_node = ast.parse(obfuscated_expr, mode='eval').body
                return obfuscated_node
            except:
                # If parsing fails, return the original node
                return node

        return node