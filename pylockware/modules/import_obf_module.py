"""
Import Obfuscation Module for PyLockWare
Obfuscates import statements using exec with string obfuscation
"""
import re
import random
import string
from pathlib import Path
from typing import Dict, Any
from pylockware.core.module_base import ModuleBase
from pylockware.core.name_generator import generate_random_name


class ImportObfuscateModule(ModuleBase):
    """
    Module that obfuscates import statements using exec with string obfuscation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.name_gen_settings = self.config.get('name_gen', 'english')
        
    def process(self, project_path: Path, output_path: Path) -> bool:
        """
        Process the project by obfuscating import statements
        
        Args:
            project_path: Path to the original project
            output_path: Path to the output directory
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            print("Applying import obfuscation to all Python files...")

            # Find all Python files in the output directory
            for py_file in output_path.rglob("*.py"):
                # Skip anti-debug modules and the obfuscator script itself
                if py_file.name not in ["anti_debug_injector.py", "anti_debug_injector_normal.py", "obfuscator.py"]:
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            original_code = f.read()

                        # Apply import obfuscation
                        obfuscated_code = self.obfuscate_imports(original_code)

                        # Only write if changes were made
                        if obfuscated_code != original_code:
                            with open(py_file, 'w', encoding='utf-8') as f:
                                f.write(obfuscated_code)

                            # Count obfuscated imports
                            original_imports = len(re.findall(r'^\s*(import|from)', original_code, re.MULTILINE))
                            obfuscated_imports = len(re.findall(r'exec\(', obfuscated_code))
                            print(f"Obfuscated {obfuscated_imports} imports in {py_file}")

                    except Exception as e:
                        print(f"Error applying import obfuscation to {py_file}: {e}")
                        
            return True
        except Exception as e:
            print(f"Error during import obfuscation: {e}")
            return False
    
    def validate_config(self) -> bool:
        """
        Validate the module's configuration
        
        Returns:
            True if configuration is valid, False otherwise
        """
        # Import obfuscation module doesn't have specific validation requirements
        return True
    
    def obfuscate_imports(self, code: str) -> str:
        """
        Obfuscate import statements in the code by wrapping them in exec with obfuscated strings
        """
        lines = code.split('\n')
        new_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Check if this is an import statement
            if stripped.startswith('import ') or stripped.startswith('from '):
                # Preserve the original indentation
                indent = line[:len(line)-len(line.lstrip())]
                
                # Create a random variable name for the import string
                import_var = self._generate_random_name()
                
                # Obfuscate the import statement string
                obfuscated_string = self._obfuscate_string(stripped)
                
                # Create the obfuscated import statement with proper indentation
                new_lines.append(f"{indent}{import_var} = {obfuscated_string}")
                new_lines.append(f"{indent}exec({import_var})")
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def _obfuscate_string(self, s: str) -> str:
        """
        Obfuscate a string using join method with character codes
        """
        # Convert string to list of character codes
        char_codes = [ord(c) for c in s]
        codes_list = '[' + ', '.join(map(str, char_codes)) + ']'
        return f"(''.join(chr(i) for i in {codes_list}))"
    
    def _generate_random_name(self) -> str:
        """
        Generate a random variable name
        """
        # Using a fixed length of 12 (average of 8 and 15) since we removed length parameter
        from pylockware.core.name_generator import generate_random_name
        return generate_random_name("_", self.name_gen_settings)