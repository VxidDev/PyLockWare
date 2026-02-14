"""
Anti-Debug Module for PyLockWare
Adds anti-debug and anti-injection protection to the project
"""
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

        # Determine which anti-debug module to use based on the setting
        if self.mode == 'native':
            module_name = 'native_anti_debug_injector'
        elif self.mode == 'normal':
            module_name = 'anti_debug_injector_normal'
        else:  # Default to strict if not specified or if 'strict'
            module_name = 'anti_debug_injector'

        # Create the protection code to add at the top of the file
        protection_code = f'''import sys
import os
# Anti-debug and anti-injection protection
try:
    from {module_name} import enable_protection
    enable_protection()
except ImportError:
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

        # Determine which anti-debug module to use based on the setting
        if self.mode == 'native':
            module_name = 'native_anti_debug_injector'
        elif self.mode == 'normal':
            module_name = 'anti_debug_injector_normal'
        else:  # Default to strict if not specified or if 'strict'
            module_name = 'anti_debug_injector'

        # Create the protection code to add at the very beginning
        protection_code = f'''# Anti-debug and anti-injection protection
import os
try:
    from {module_name} import enable_protection
    enable_protection()
except ImportError:
    while True:
        os._exit(1)

'''

        # Check if protection is already added
        if "# Anti-debug and anti-injection protection" in content:
            return  # Already added

        # Add protection at the very beginning of the file
        new_content = protection_code + content

        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)