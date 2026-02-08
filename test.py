#!/usr/bin/env python3
"""
Обфускатор импортов Python
Превращает все статические импорты в динамические через __import__()
"""

import ast
import sys
import random
import string
from pathlib import Path


def generate_random_name(length=8):
    """Генерация случайного имени переменной"""
    # Используем другой формат, чтобы избежать конфликта с именами, созданными ремапом (_gN)
    return '_imp_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def obfuscate_imports(source_code):
    """
    Преобразует все импорты в динамические через __import__()
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        print(f"Ошибка парсинга: {e}")
        return None

    # Собираем все импорты
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    'type': 'import',
                    'module': alias.name,
                    'asname': alias.asname,
                    'lineno': node.lineno,
                    'end_lineno': node.end_lineno
                })
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports.append({
                    'type': 'from',
                    'module': module,
                    'name': alias.name,
                    'asname': alias.asname,
                    'level': node.level,
                    'lineno': node.lineno,
                    'end_lineno': node.end_lineno
                })

    if not imports:
        return source_code

    # Сортируем по позиции (с конца, чтобы замены не сдвигали индексы)
    imports.sort(key=lambda x: x['lineno'], reverse=True)

    lines = source_code.split('\n')

    # Обрабатываем каждый импорт
    obfuscated_imports = []
    for imp in imports:
        start_line = imp['lineno'] - 1
        end_line = imp['end_lineno'] - 1

        # Удаляем оригинальные строки импорта
        for i in range(start_line, end_line + 1):
            lines[i] = None

        if imp['type'] == 'import':
            # import module [as alias]
            module = imp['module']
            alias = imp['asname'] or module.split('.')[0]
            var_name = generate_random_name()

            # Главный фикс: всегда присваиваем alias
            obf_code = f"{var_name} = __import__('{module}'); {alias} = {var_name}"
            obfuscated_imports.append(obf_code)

        elif imp['type'] == 'from':
            # from module import name [as alias]
            module = imp['module']
            name = imp['name']
            alias = imp['asname'] or name
            level = imp['level']

            # Правильная обработка относительных импортов
            if level > 0:
                # Для относительных импортов (from .module или from ..module)
                if module:
                    # from .module import ...
                    full_module = '.' * level + module
                else:
                    # from . import ... (модуль пустой, только уровень)
                    full_module = '.' * level
            else:
                # Абсолютный импорт
                full_module = module

            var_name = generate_random_name()

            if name == '*':
                # from module import *
                obf_code = f"{var_name} = __import__('{full_module}', globals(), locals(), ['*'], {level}); globals().update({{k: v for k, v in {var_name}.__dict__.items() if not k.startswith('_')}})"
            else:
                # from module import name
                obf_code = f"{var_name} = __import__('{full_module}', globals(), locals(), ['{name}'], {level}); {alias} = getattr({var_name}, '{name}')"

            obfuscated_imports.append(obf_code)

    # Фильтруем удаленные строки
    lines = [line for line in lines if line is not None]

    # Добавляем случайные комментарии для маскировки
    random_comments = [
        "# " + ''.join(random.choices(string.ascii_letters + ' ', k=30))
        for _ in range(random.randint(1, 3))
    ]

    # Формируем финальный код
    header = [
        "# Obfuscated imports",
        *random_comments,
        *obfuscated_imports,
        ""
    ]

    return '\n'.join(header + lines)


def process_file(filepath, output_path=None):
    """Обработка одного файла"""
    path = Path(filepath)

    if not path.exists():
        print(f"Файл не найден: {filepath}")
        return False

    source = path.read_text(encoding='utf-8')

    obfuscated = obfuscate_imports(source)
    if obfuscated is None:
        return False

    # Определяем путь для сохранения
    if output_path:
        out_path = Path(output_path)
    else:
        out_path = path.parent / f"{path.stem}_obfuscated{path.suffix}"

    out_path.write_text(obfuscated, encoding='utf-8')
    print(f"Сохранено: {out_path}")
    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Обфускатор импортов Python')
    parser.add_argument('files', nargs='+', help='Python файлы для обфускации')
    parser.add_argument('-o', '--output', help='Папка для сохранения')
    parser.add_argument('--in-place', action='store_true', help='Заменить оригинальные файлы')

    args = parser.parse_args()

    for filepath in args.files:
        if args.in_place:
            process_file(filepath, filepath)
        else:
            process_file(filepath, args.output)


if __name__ == "__main__":
    main()