"""
Anti-Debug Module for PyLockWare
Adds anti-debug and anti-injection protection to the project
"""
import ast
import shutil
from pathlib import Path
from typing import Dict, Any
from pylockware.core.module_base import ModuleBase


class AntiDebugModule(ModuleBase):
    """
    Module that adds anti-debug and anti-injection protection to the project
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.mode = self.config.get('mode', 'native')  # Can be 'normal', 'strict', or 'native'

    def process(self, project_path: Path, output_path: Path) -> bool:
        """
        Process the project by adding anti-debug protection

        Args:
            project_path: Path to the original project
            output_path: Path to the output directory

        Returns:
            True if processing was successful, False otherwise
        """
        import platform
        import sys

        try:
            # Check if running on Windows AMD64
            if not (sys.platform == 'win32' and platform.machine().lower() in ['amd64', 'x86_64']):
                print("Anti-debug protection is only enabled for Windows AMD64 - skipping...")
                return True

            # Determine which anti-debug module to use based on the mode
            if self.mode == 'native':
                # Use the native anti-debug module
                protection_module_path = output_path / "native_anti_debug_injector.py"
                module_path = Path(__file__).parent.parent / 'anti_debug' / 'native_anti_debug_injector.py'
                shutil.copy(str(module_path), str(protection_module_path))
                
                # Also copy the native DLL to the output directory
                # First, try to find the DLL in the expected location relative to the project
                dll_source_path = Path(__file__).parent.parent.parent / 'native_src' / 'PyLockWareRuntime' / 'x64' / 'Release' / 'PyLockWareRuntime.dll'
                
                # If not found in the expected location, try to find it in the current working directory
                if not dll_source_path.exists():
                    dll_source_path = Path('PyLockWareRuntime.dll')
                    
                # If still not found, try to find it in the system path
                if not dll_source_path.exists():
                    dll_source_path = 'PyLockWareRuntime.dll'
                
                dll_output_path = output_path / 'PyLockWareRuntime.dll'
                
                # Try to copy the DLL to the output directory
                try:
                    if isinstance(dll_source_path, Path) and dll_source_path.exists():
                        shutil.copy(str(dll_source_path), str(dll_output_path))
                    else:
                        # If we can't find the DLL at the expected path, try to copy from the current working directory
                        try:
                            shutil.copy('PyLockWareRuntime.dll', str(dll_output_path))
                        except FileNotFoundError:
                            pass  # Silently fail if DLL not found
                except Exception:
                    pass  # Silently fail if there's an error copying DLL
            elif self.mode == 'normal':
                # Copy the normal anti-debug module
                protection_module_path = output_path / "anti_debug_injector_normal.py"
                module_path = Path(__file__).parent.parent / 'anti_debug' / 'anti_debug_injector_normal.py'
                shutil.copy(str(module_path), str(protection_module_path))
            else:  # Default to strict if not specified or if 'strict'
                # Copy the strict anti-debug module
                protection_module_path = output_path / "anti_debug_injector.py"
                module_path = Path(__file__).parent.parent / 'anti_debug' / 'anti_debug_injector.py'
                shutil.copy(str(module_path), str(protection_module_path))

            # Get all Python modules in the output directory
            modules = []
            for py_file in output_path.rglob("*.py"):
                # Include all Python files except the obfuscator script itself
                if py_file.name != "obfuscator.py":
                    modules.append(py_file)

            # Add protection to the entry point file first (assuming it's specified in config)
            entry_point = self.config.get('entry_point')
            if entry_point:
                entry_point_path = output_path / entry_point
                self.add_anti_debug_protection_to_entry_point(entry_point_path)

            # Add protection to each module
            for module in modules:
                # Don't add protection to the anti-debug modules themselves
                if module.name not in ["anti_debug_injector.py", "anti_debug_injector_normal.py", "native_anti_debug_injector.py"]:
                    self.add_anti_debug_protection(module)

            return True
        except Exception as e:
            print(f"Error during anti-debug protection: {e}")
            return False

    def validate_config(self) -> bool:
        """
        Validate the module's configuration

        Returns:
            True if configuration is valid, False otherwise
        """
        if self.mode not in ['normal', 'strict', 'native']:
            print(f"Invalid anti-debug mode: {self.mode}. Valid options are 'normal', 'strict', or 'native'.")
            return False
        return True

    def add_anti_debug_protection(self, file_path: Path):
        """
        Add anti-debug and anti-injection protection to a file
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if protection is already added
        if "# Anti-debug and anti-injection protection" in content:
            return  # Already added

        # Parse the AST to find import positions
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # If we can't parse the file, add protection at the beginning
            self._add_protection_at_beginning(file_path, content)
            return

        # Find the position after PySide6/PyQt imports
        insert_pos = self._find_import_insert_position(tree, content)

        # Determine which anti-debug module to use based on the setting
        if self.mode == 'native':
            module_name = 'native_anti_debug_injector'
        elif self.mode == 'normal':
            module_name = 'anti_debug_injector_normal'
        else:  # Default to strict if not specified or if 'strict'
            module_name = 'anti_debug_injector'

        # Create the protection code
        protection_code = f'''# Anti-debug and anti-injection protection
try:
    from {module_name} import enable_protection
    enable_protection()
except ImportError:
    import os
    while True:
        os._exit(1)

'''

        # Insert the protection code at the determined position
        lines = content.split('\n')
        
        # Find the line number corresponding to insert_pos
        line_num = 0
        char_count = 0
        for i, line in enumerate(lines):
            if char_count >= insert_pos:
                line_num = i
                break
            char_count += len(line) + 1  # +1 for newline character
        
        # Insert the protection code after the imports
        new_lines = lines[:line_num] + [protection_code.rstrip()] + [''] + lines[line_num:]
        new_content = '\n'.join(new_lines)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

    def _find_import_insert_position(self, tree, content):
        """
        Find the position to insert anti-debug code after PySide6/PyQt imports
        If no such imports exist, return position after all imports at the beginning
        """
        lines = content.split('\n')
        
        # First, check if there are any PySide6/PyQt imports
        pyside_pyqt_imports = []
        all_imports = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                line_start = node.lineno - 1  # Convert to 0-indexed
                # Calculate the end line of the import statement (accounting for multiline imports)
                line_end = line_start
                
                # For multiline imports, we need to find where the import statement ends
                if hasattr(node, 'end_lineno'):  # Available in Python 3.8+
                    line_end = node.end_lineno - 1
                else:
                    # Fallback for older Python versions - scan for end of statement
                    line_end = line_start
                    current_line_idx = line_start
                    paren_depth = 0
                    
                    # Count parentheses to find end of multiline statement
                    for i in range(line_start, min(len(lines), line_start + 20)):  # Limit search to 20 lines
                        line = lines[i]
                        for char in line:
                            if char == '(':
                                paren_depth += 1
                            elif char == ')':
                                paren_depth -= 1
                        if paren_depth <= 0 and not line.rstrip().endswith('\\'):
                            line_end = i
                            break
                        elif not line.rstrip().endswith('\\') and paren_depth <= 0:
                            line_end = i
                            break
                
                all_imports.append((node, line_start, line_end))
                
                # Check if this is a PySide6 or PyQt import
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith(('PySide', 'PyQt')):
                            pyside_pyqt_imports.append((node, line_start, line_end))
                            break
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith(('PySide', 'PyQt')):
                        pyside_pyqt_imports.append((node, line_start, line_end))
        
        # If PySide6/PyQt imports were found, return position after the last one
        if pyside_pyqt_imports:
            # Get the ending line number of the last PySide/PyQt import
            last_pyside_pyqt_end_line = max(end_line for _, _, end_line in pyside_pyqt_imports)
            # Calculate the character position after that line
            pos_after_last_pyside_pyqt = sum(len(lines[i]) + 1 for i in range(last_pyside_pyqt_end_line + 1))
            return pos_after_last_pyside_pyqt
        
        # If no PySide6/PyQt imports found, return position after all initial imports
        if all_imports:
            # Find the last import in sequence at the beginning
            last_import_end_line = 0
            for node, line_start, line_end in all_imports:
                if line_start <= last_import_end_line + 1:  # Allow one blank line between imports
                    last_import_end_line = line_end
                else:
                    # Gap in imports, stop here
                    break
            
            # Calculate position after the last contiguous import
            pos_after_imports = sum(len(lines[i]) + 1 for i in range(last_import_end_line + 1))
            return pos_after_imports
        
        # If no imports at all, return 0 (beginning of file)
        return 0

    def _is_whitespace_or_comment(self, line):
        """Check if a line is whitespace or a comment"""
        stripped = line.strip()
        return stripped == '' or stripped.startswith('#')

    def _add_protection_at_beginning(self, file_path, content):
        """
        Fallback method to add protection at the beginning of the file
        """
        # Determine which anti-debug module to use based on the setting
        if self.mode == 'native':
            module_name = 'native_anti_debug_injector'
        elif self.mode == 'normal':
            module_name = 'anti_debug_injector_normal'
        else:  # Default to strict if not specified or if 'strict'
            module_name = 'anti_debug_injector'

        # Create the protection code to add at the top of the file
        protection_code = f'''# Anti-debug and anti-injection protection
try:
    from {module_name} import enable_protection
    enable_protection()
except ImportError:
    import os
    while True:
        os._exit(1)

'''

        # Check if protection is already added
        if "# Anti-debug and anti-injection protection" in content:
            return  # Already added

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(protection_code + content)

    def add_anti_debug_protection_to_entry_point(self, file_path: Path):
        """
        Add anti-debug protection specifically to the entry point file
        """
        # Read the current content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if protection is already added
        if "# Anti-debug and anti-injection protection" in content:
            return  # Already added

        # Parse the AST to find import positions
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # If we can't parse the file, add protection at the beginning
            self._add_protection_at_beginning(file_path, content)
            return

        # Find the position after PySide6/PyQt imports
        insert_pos = self._find_import_insert_position(tree, content)

        # Determine which anti-debug module to use based on the setting
        if self.mode == 'native':
            module_name = 'native_anti_debug_injector'
        elif self.mode == 'normal':
            module_name = 'anti_debug_injector_normal'
        else:  # Default to strict if not specified or if 'strict'
            module_name = 'anti_debug_injector'

        # Create the protection code
        protection_code = f'''# Anti-debug and anti-injection protection
try:
    from {module_name} import enable_protection
    enable_protection()
except ImportError:
    import os
    while True:
        os._exit(1)

'''

        # Insert the protection code at the determined position
        lines = content.split('\n')
        
        # Find the line number corresponding to insert_pos
        line_num = 0
        char_count = 0
        for i, line in enumerate(lines):
            if char_count >= insert_pos:
                line_num = i
                break
            char_count += len(line) + 1  # +1 for newline character
        
        # Insert the protection code after the imports
        new_lines = lines[:line_num] + [protection_code.rstrip()] + [''] + lines[line_num:]
        new_content = '\n'.join(new_lines)

        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)