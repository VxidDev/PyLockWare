# PyLockWare - Advanced Python Obfuscation Suite

PyLockWare is a comprehensive Python obfuscation tool designed to protect your source code from reverse engineering and unauthorized access. It provides multiple layers of protection through advanced obfuscation techniques, anti-debugging mechanisms, and code transformation methods.

## 🚀 Features

- **Identifier Remapping**: Renames functions, classes, variables, and attributes to random, meaningless names
- **String Protection**: Encodes string literals using base64 and zlib compression to prevent easy extraction
- **Number Obfuscation**: Transforms numeric constants into complex arithmetic expressions
- **Import Obfuscation**: Hides import statements using dynamic execution techniques
- **State Machine Obfuscation**: Transforms functions into state machines to obfuscate control flow
- **Builtin Dispatcher Obfuscation**: Replaces built-in function calls (print, len, input, etc.) with calls via a dispatcher class using obfuscated names
- **Junk Code Generation**: Adds fake if/elif branches with opaque predicates that always evaluate to True or False
- **Disable Traceback**: Hides error details by setting sys.tracebacklimit = 0 at the start of each file
- **Configurable Name Generators**: Customizable character sets for generated obfuscated names (English, Chinese, mixed, numbers, hex)
- **Configurable Opaque Predicates**: Multiple complexity levels for junk code conditions (Low, Medium, High)
- **Anti-Debug Protection**: Windows AMD64 only, very unstable, especially with nuitka.
- **Multi-Platform Support**: Works across Windows, macOS, and Linux
- **Dual Interface**: Both command-line and graphical user interfaces
- **Preserves Functionality**: Maintains original program behavior while protecting the source code
- **Nuitka EXE Packaging**: Built-in support for compiling obfuscated code to standalone executables

## 📋 Requirements

- Python 3.7 or higher
- Dependencies:
  - `psutil` (~=7.2.2)
  - `pywin32` (~=311) - Windows only
  - `PySide6` (~=6.10.2)

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/amogus-gggy/PyLockWare.git
   cd PyLockWare
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Usage

### Graphical User Interface (GUI)

Launch the intuitive GUI for easy configuration:

```bash
python gui.py
```

The GUI provides:
- Project path selection
- Configuration options for each obfuscation technique
- State machine obfuscation to transform functions into state machines
- Configurable name generators with multiple character sets (English, Chinese, mixed, numbers, hex)
- Real-time preview of settings
- One-click obfuscation process

### Command-Line Interface (CLI)

For automation and integration into build processes:

```bash
python cli.py /path/to/your/project --entry-point main.py [options]
```

#### CLI Options

| Option | Description |
|--------|-------------|
| `--entry-point` | Entry point file of the project (required) |
| `--entry-function` | Main function name in the entry point (default: main) |
| `--banner` | Banner text to add to modules (default: "Obfuscated by PyLockWare Obfuscator") |
| `--output-dir` | Output directory for obfuscated project (default: dist) |
| `--remap` | Enable renaming of functions, variables, etc. to random names |
| `--anti-debug {normal,strict,native}` | Enable anti-debug and anti-injection protection |
| `--string-prot` | Enable string protection using base64 and zlib encoding |
| `--num-obf` | Enable number obfuscation using arithmetic expressions |
| `--import-obf` | Enable import obfuscation using dynamic execution techniques |
| `--state-machine` | Enable state machine obfuscation to transform functions into state machines |
| `--builtin-dispatcher` | Enable builtin dispatcher obfuscation to replace built-in calls with dispatcher calls |
| `--junk-code` | Enable junk code generation with fake if/elif branches |
| `--junk-density {0.0-1.0}` | Junk code density from 0.0 to 1.0 (default: 0.5) |
| `--opaque-complexity {low,medium,high}` | Complexity level of opaque predicates (default: high) |
| `--disable-traceback` | Disable traceback by setting sys.tracebacklimit = 0 at the start of each file |
| `--name-gen {english,chinese,mixed,numbers,hex}` | Character set for name generation (default: english) |

#### Example Usage

Basic obfuscation with all protections enabled:
```bash
python cli.py /path/to/project --entry-point main.py --remap --string-prot --num-obf --import-obf --anti-debug strict
```

Obfuscation with junk code and opaque predicates:
```bash
python cli.py /path/to/project --entry-point main.py --remap --junk-code --junk-density 0.7 --opaque-complexity high
```

Obfuscation with traceback disabled (hides error details):
```bash
python cli.py /path/to/project --entry-point main.py --remap --string-prot --disable-traceback
```

Full obfuscation with all features including state machine and junk code:
```bash
python cli.py /path/to/project --entry-point main.py --remap --string-prot --num-obf --state-machine --builtin-dispatcher --junk-code --junk-density 0.8 --opaque-complexity high
```

Light obfuscation with only identifier remapping:
```bash
python cli.py /path/to/project --entry-point main.py --remap
```

Custom output directory:
```bash
python cli.py /path/to/project --entry-point main.py --remap --output-dir ./protected_build
```

## 🔧 How It Works

PyLockWare uses an AST (Abstract Syntax Tree) based approach to transform your Python code:

1. **Parsing**: The source code is parsed into an AST representation
2. **Transformation**: Multiple transformation passes apply different obfuscation techniques
3. **Code Generation**: The transformed AST is converted back to Python source code
4. **Protection Layering**: Additional protection mechanisms are applied as needed

Each obfuscation technique operates independently, allowing for flexible configuration based on your security needs and performance requirements.

## 🛡️ Protection Techniques

### Identifier Remapping
Transforms meaningful variable and function names into random sequences, making code analysis significantly more difficult.

### String Protection
Encodes string literals to prevent easy extraction of sensitive information like API keys, file paths, or hardcoded values.

### Number Obfuscation
Converts numeric constants into complex mathematical expressions, hiding important numerical values.

### Import Obfuscation
Hides import statements using dynamic execution, making dependency analysis more challenging.

### Anti-Debug Protection
Implements runtime checks to detect and prevent debugging attempts, with three modes:
- **Normal**: Basic detection of common debugging tools
- **Strict**: Enhanced detection including thread monitoring
- **Native**: High-performance protection using native DLL implementation for maximum security

### State Machine Obfuscation
Transforms functions into state machines to obfuscate control flow, making it significantly harder to analyze and understand the program's logic by converting sequential code into a series of state transitions.

### Builtin Dispatcher Obfuscation
Replaces built-in function calls (such as `print()`, `len()`, `input()`, `open()`, etc.) with calls through a dispatcher class using obfuscated names. This makes it harder to identify which built-in functions are being used in the code.

**Example:**
```python
# Before obfuscation:
print("Hello, World!")
result = len(items)

# After obfuscation:
from _builtin_dispatcher import _abc123 as _XyZ789
_XyZ789.ghJkLm("Hello, World!")
result = _XyZ789.NoPqRs(items)
```

The dispatcher is automatically created and copied to each package directory, ensuring proper imports regardless of the module's location in the project structure.

### Junk Code Generation
Adds fake if/elif branches with opaque predicates that always evaluate to True or False. These branches contain dead code that never executes but significantly complicates code analysis and reverse engineering.

**Features:**
- **Opaque Predicates**: Complex conditions that always evaluate to True or False (e.g., `pow(x, 0) == 1`, `(x ^ y) ^ y == x`, `chr(ord('A')) == 'A'`)
- **Configurable Density**: Control how much junk code is added (0.0 to 1.0)
- **Multiple Complexity Levels**: 
  - **Low**: Simple mathematical identities
  - **Medium**: More complex expressions and built-in function calls
  - **High**: Very complex predicates with nested conditions and boolean combinations

**Example opaque predicates:**
```python
# Always True:
(x * 2) // 2 == x
pow(7, 0) == 1
(x ^ y) ^ y == x
chr(ord('A')) == 'A'
sum([1, 2, 3]) == 6

# Always False:
pow(42, 1) != 42
"abc" in "def"
isinstance(42, str)
sum([1, 2, 3]) != 6
```

### Configurable Name Generators
Provides customizable character sets for generating obfuscated names, including:
- **English**: Standard Latin letters and digits
- **Chinese**: Chinese Unicode characters
- **Mixed**: Combination of English and Chinese characters
- **Numbers**: Numeric digits only
- **Hex**: Hexadecimal characters (0-9, A-F)



## 🧪 Testing Your Obfuscated Code

After obfuscation, always test your protected code to ensure it functions correctly:

1. Navigate to the output directory
2. Run your application with the same inputs used in the original version
3. Verify all features work as expected
4. Check for any performance impacts

## ⚠️ Important Notes

- Always keep a backup of your original source code
- Test thoroughly after obfuscation to ensure functionality is preserved
- Heavier obfuscation may impact runtime performance
- Some antivirus software may flag anti-debug protections as suspicious
- The obfuscated code remains Python and can theoretically be reversed with sufficient effort


### Recommended Workflow for EXE Distribution

1. Obfuscate your Python code with PyLockWare (without anti-debug/import-obf)
2. Package with Nuitka into a standalone EXE
3. Apply a native protector (Themida/VMProtect) to the resulting EXE

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the AGPLv3 License - see the LICENSE file for details.

## 🐛 Issues and Support

If you encounter any problems or have suggestions for improvements, please open an issue on GitHub.
