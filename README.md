# PyLockWare - Advanced Python Obfuscation Suite

PyLockWare is a comprehensive Python obfuscation tool designed to protect your source code from reverse engineering and unauthorized access. It provides multiple layers of protection through advanced obfuscation techniques, anti-debugging mechanisms, and code transformation methods.

## 🚀 Features

- **Identifier Remapping**: Renames functions, classes, variables, and attributes to random, meaningless names
- **String Protection**: Encodes string literals using base64 and zlib compression to prevent easy extraction
- **Number Obfuscation**: Transforms numeric constants into complex arithmetic expressions
- **Import Obfuscation**: Hides import statements using dynamic execution techniques
- **Anti-Debug Protection**: Implements sophisticated anti-debugging and anti-injection mechanisms
  - Normal mode: Basic protection against common debugging tools
  - Strict mode: Enhanced protection with thread monitoring
- **Multi-Platform Support**: Works across Windows, macOS, and Linux
- **Dual Interface**: Both command-line and graphical user interfaces
- **Preserves Functionality**: Maintains original program behavior while protecting the source code

## 📋 Requirements

- Python 3.7 or higher
- Dependencies:
  - `psutil` (~=7.2.2)
  - `pywin32` (~=311) - Windows only
  - `PySide6` (~=6.10.2)

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/PyLockWare.git
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
| `--anti-debug {normal,strict}` | Enable anti-debug and anti-injection protection |
| `--string-prot` | Enable string protection using base64 and zlib encoding |
| `--num-obf` | Enable number obfuscation using arithmetic expressions |
| `--import-obf` | Enable import obfuscation using dynamic execution techniques |

#### Example Usage

Basic obfuscation with all protections enabled:
```bash
python cli.py /path/to/project --entry-point main.py --remap --string-prot --num-obf --import-obf --anti-debug strict
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
Implements runtime checks to detect and prevent debugging attempts, with two modes:
- **Normal**: Basic detection of common debugging tools
- **Strict**: Enhanced detection including thread monitoring

## 📁 Project Structure

```
pylockware/
├── core/                 # Core obfuscator logic
│   └── obfuscator.py     # Main obfuscator class
├── modules/              # Individual obfuscation modules
│   ├── remap_module.py          # Identifier remapping
│   ├── string_protect_module.py # String protection
│   ├── number_obf_module.py     # Number obfuscation
│   ├── import_obf_module.py     # Import obfuscation
│   └── anti_debug_module.py     # Anti-debug protection
├── gui/                  # Graphical user interface
│   └── obfuscator_gui.py # GUI implementation
└── cli/                  # Command-line interface
```

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

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the AGPLv3 License - see the LICENSE file for details.

## 🐛 Issues and Support

If you encounter any problems or have suggestions for improvements, please open an issue on GitHub.