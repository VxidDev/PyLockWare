# PyLockWare - Python Obfuscation Suite

A comprehensive tool for obfuscating Python code with multiple protection layers.

## Project Structure

```
pylockware/
├── core/                 # Main obfuscator logic
│   └── obfuscator.py     # Main obfuscator class
├── transforms/           # AST transformation modules
│   ├── remap_transformer.py  # Identifier remapping
│   └── str_prot.py       # String protection
├── anti_debug/           # Anti-debugging/injection modules
│   ├── anti_debug_injector.py        # Strict anti-debug protection
│   └── anti_debug_injector_normal.py # Normal anti-debug protection
├── gui/                  # Graphical user interface
│   └── obfuscator_gui.py # GUI implementation
└── cli/                  # Command-line interface (future use)
```

## Entry Points

- `gui.py` - Launch the graphical user interface
- `cli.py` - Launch the command-line interface

## Features

- **Identifier Remapping**: Renames functions, classes, and variables to random names
- **String Protection**: Encodes string literals using base64 and zlib
- **Anti-Debug Protection**: Prevents debugging and code injection
- **GUI Interface**: Easy-to-use graphical interface
- **CLI Interface**: Command-line interface for automation

## Usage

### GUI Mode
```bash
python gui.py
```

### CLI Mode
```bash
python cli.py /path/to/project --entry-point main.py --remap --string-prot --anti-debug strict
```

## Requirements

- Python 3.7+
- PySide6 (for GUI)
- psutil
- pywin32 (on Windows)

See `requirements.txt` for the full list of dependencies.