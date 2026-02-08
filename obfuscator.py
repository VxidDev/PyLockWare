"""
Simple Python Obfuscator Base
"""

import ast
import os
import sys
import argparse
import shutil
import random
import string
from pathlib import Path
from typing import Set, List, Dict, Any

from remap_transformer import GlobalRenamer
from test import obfuscate_imports



class PyObfuscator:
    """
    A simple Python obfuscator base class
    """

    def __init__(self, project_path: str, entry_point: str, entry_function: str = "main", output_dir: str = "dist", remap: bool = False, anti_debug: str = None, obfuscate_imports: bool = False):
        self.project_path = Path(project_path)
        self.entry_point = Path(entry_point)
        self.entry_function = entry_function
        self.output_dir = Path(output_dir)
        self.remap = remap
        self.anti_debug = anti_debug  # Can be None, 'normal', or 'strict'
        self.obfuscate_imports = obfuscate_imports
        self.imports_whitelist = set()
        self.modules_to_obfuscate = []
        self.remap_map = {}  # Store mapping of original names to obfuscated names
        
    def validate_paths(self):
        """
        Validate that the project path and entry point exist
        """
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {self.project_path}")
            
        # Convert entry_point to Path if it isn't already
        if isinstance(self.entry_point, str):
            self.entry_point = Path(self.entry_point)
        
        full_entry_path = self.project_path / self.entry_point
        if not full_entry_path.exists():
            raise FileNotFoundError(f"Entry point does not exist: {full_entry_path}")
    
    def collect_imports_recursive(self, file_path: Path) -> Set[str]:
        """
        Recursively collect all imports from a Python file
        """
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
                        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return imports
    
    def build_imports_whitelist(self):
        """
        Build a whitelist of imports that should not be obfuscated
        """
        if not self.entry_point:
            raise ValueError("Entry point not detected")
            
        # Collect imports from the original entry point
        original_entry_point = self.project_path / self.entry_point
        imports = self.collect_imports_recursive(original_entry_point)
        self.imports_whitelist.update(imports)
        
        # For now, just add the entry point's imports to whitelist
        # In a more advanced version, we could recursively follow imports
    
    def generate_random_name(self, counter: int) -> str:
        """
        Generate a random name for remapping
        Names must start with a letter or underscore to be valid Python identifiers
        """
        return f"_g{counter}"
    
    def build_global_replacements(self, directory: Path):
        """
        Build a mapping of original names to obfuscated names for the entire project
        """
        py_files = list(directory.rglob("*.py"))
        counter = 0

        # First, collect module filenames and directory names
        all_names = set()
        
        # Also collect module names used in import statements to protect them from remapping
        imported_module_names = set()

        # First pass: collect all module names used in imports
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            # Get the top-level module name
                            module_name = alias.name.split(".")[0]
                            imported_module_names.add(module_name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            # Get the top-level module name for from imports too
                            module_name = node.module.split(".")[0]
                            imported_module_names.add(module_name)
            except Exception:
                continue  # If we can't parse a file, just skip it for import detection

        for py_file in py_files:
            # Include all .py files, including __init__.py files
            if py_file.name != "__main__.py":
                # Extract module name from the file path
                # For __init__.py files, use the parent directory name
                if py_file.name == "__init__.py":
                    module_name = py_file.parent.name
                else:
                    module_name = py_file.stem

                if (
                    module_name
                    and not module_name.startswith("_")
                    and not self._is_external_module(module_name)
                    and 'anti_debug' not in module_name  # Skip anti-debug modules
                    and module_name not in imported_module_names  # Skip if used in imports
                ):
                    all_names.add(module_name)

                # Add directory names from the path (excluding root directory)
                # Get the relative path from the project root
                rel_path = py_file.relative_to(directory)
                # Add each directory component in the path
                for part in rel_path.parts[:-1]:  # Exclude the filename itself
                    if (part
                        and not part.startswith("_")
                        and not self._is_external_module(part)
                        and 'anti_debug' not in part  # Skip anti-debug related dirs
                        and part not in imported_module_names):  # Skip if used in imports
                        all_names.add(part)

        # Now assign remap names to all collected names
        for name in sorted(all_names):  # Sort for consistent ordering
            # Skip names that look like they were generated by import obfuscation
            if name not in self.remap_map and not name.startswith('_imp_'):
                self.remap_map[name] = self.generate_random_name(counter)
                counter += 1

        # Process all Python files to collect functions, classes, and other identifiers
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                
                # Check if this is an anti-debug file
                is_anti_debug_file = 'anti_debug' in str(py_file)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                        if node.name not in self.imports_whitelist and node.name != self.entry_function:
                            # Skip names that look like they were generated by import obfuscation
                            # Skip names in anti-debug files
                            # Skip names that are module names used in imports
                            if (not node.name.startswith('_imp_') 
                                and node.name not in self.remap_map 
                                and not is_anti_debug_file
                                and node.name not in imported_module_names):
                                self.remap_map[node.name] = self.generate_random_name(counter)
                                counter += 1
                    elif isinstance(node, ast.AsyncFunctionDef) and not node.name.startswith("_"):
                        if node.name not in self.imports_whitelist and node.name != self.entry_function:
                            # Skip names that look like they were generated by import obfuscation
                            # Skip names in anti-debug files
                            # Skip names that are module names used in imports
                            if (not node.name.startswith('_imp_') 
                                and node.name not in self.remap_map 
                                and not is_anti_debug_file
                                and node.name not in imported_module_names):
                                self.remap_map[node.name] = self.generate_random_name(counter)
                                counter += 1
                    elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                        if node.name not in self.imports_whitelist:
                            # Skip names that look like they were generated by import obfuscation
                            # Skip names in anti-debug files
                            # Skip names that are module names used in imports
                            if (not node.name.startswith('_imp_') 
                                and node.name not in self.remap_map 
                                and not is_anti_debug_file
                                and node.name not in imported_module_names):
                                self.remap_map[node.name] = self.generate_random_name(counter)
                                counter += 1
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and not target.id.startswith("_"):
                                # Skip names that look like they were generated by import obfuscation
                                # Skip names in anti-debug files
                                # Skip names that are module names used in imports
                                if (target.id not in self.imports_whitelist 
                                    and not target.id.startswith('_imp_')
                                    and not is_anti_debug_file
                                    and target.id not in imported_module_names):
                                    if target.id not in self.remap_map:
                                        self.remap_map[target.id] = self.generate_random_name(counter)
                                        counter += 1
                    elif isinstance(node, ast.AnnAssign):
                        if isinstance(node.target, ast.Name) and not node.target.id.startswith("_"):
                            # Skip names that look like they were generated by import obfuscation
                            # Skip names in anti-debug files
                            # Skip names that are module names used in imports
                            if (node.target.id not in self.imports_whitelist 
                                and not node.target.id.startswith('_imp_')
                                and not is_anti_debug_file
                                and node.target.id not in imported_module_names):
                                if node.target.id not in self.remap_map:
                                    self.remap_map[node.target.id] = self.generate_random_name(counter)
                                    counter += 1
                    elif isinstance(node, ast.Import):
                        # Handle import aliases (e.g., import module as alias)
                        for alias in node.names:
                            # If there's an alias (import module as alias), we should remap the alias
                            if alias.asname and not alias.asname.startswith("_"):
                                # Skip names that look like they were generated by import obfuscation
                                # Also skip names that are anti-debug modules
                                # Also skip names in anti-debug files
                                # Also skip names that are module names used in imports
                                is_anti_debug_alias = alias.name and ('anti_debug' in alias.name)
                                if (alias.asname not in self.imports_whitelist 
                                    and not alias.asname.startswith('_imp_')
                                    and not is_anti_debug_alias
                                    and not is_anti_debug_file
                                    and alias.asname not in imported_module_names):
                                    if alias.asname not in self.remap_map:
                                        self.remap_map[alias.asname] = self.generate_random_name(counter)
                                        counter += 1
                            else:
                                # If there's no alias (just 'import module'), we shouldn't remap the module name
                                # because it would break the import - the module name in expressions should stay the same
                                module_name = alias.name.split(".")[0]  # Take the top-level module name
                                # Add the module name to remap_map with the same value to prevent renaming
                                if module_name not in self.remap_map:
                                    self.remap_map[module_name] = module_name
                    elif isinstance(node, ast.ImportFrom):
                        # Handle from ... import ... aliases
                        for alias in node.names:
                            if alias.asname and not alias.asname.startswith("_"):
                                # Skip names that look like they were generated by import obfuscation
                                # Also skip names imported from anti-debug modules
                                # Also skip if in anti-debug file
                                # Also skip names that are module names used in imports
                                is_anti_debug_import = node.module and ('anti_debug' in node.module)
                                if (alias.asname not in self.imports_whitelist 
                                    and not alias.asname.startswith('_imp_') 
                                    and not is_anti_debug_import
                                    and not is_anti_debug_file
                                    and alias.asname not in imported_module_names):
                                    if alias.asname not in self.remap_map:
                                        self.remap_map[alias.asname] = self.generate_random_name(counter)
                                        counter += 1
                            else:
                                # If importing without an alias (from module import name),
                                # we don't want to remap the imported name
                                # But we also need to make sure the module name isn't remapped in certain contexts
                                pass
                        # For 'from module import ...', we don't remap the module name itself
                        # because it's only used in the import statement
                                    
            except Exception as e:
                print(f"Error processing {py_file}: {e}")
    
    def _is_external_module(self, module_name: str) -> bool:
        """Check if a module is external (stdlib or pip package)."""
        # Hardcoded list of common standard library modules
        stdlib_modules = {
            "sys", "os", "json", "datetime", "pathlib", "time", "random", "math",
            "collections", "typing", "base64", "zlib", "numpy", "requests", "urllib",
            "http", "email", "html", "xml", "sqlite3", "logging", "unittest", "argparse",
            "configparser", "tempfile", "shutil", "glob", "fnmatch", "re", "string",
            "textwrap", "struct", "codecs", "pickle", "csv", "hashlib", "hmac", "secrets",
            "uuid", "socket", "ssl", "ftplib", "poplib", "imaplib", "smtplib", "telnetlib",
            "urllib", "http", "email", "mimetypes", "zipfile", "tarfile", "linecache",
            "shlex", "platform", "errno", "stat", "filecmp", "fileinput", "calendar",
            "zoneinfo", "getopt", "getpass", "curses", "ctypes", "threading", "multiprocessing",
            "concurrent", "subprocess", "sched", "queue", "contextlib", "asyncio", "select",
            "selectors", "asyncore", "asynchat", "signal", "mmap", "pipes", "resource",
            "posix", "pwd", "spwd", "grp", "crypt", "termios", "tty", "pty", "fcntl",
            "io", "sysconfig", "warnings", "traceback", "faulthandler", "gc", "inspect",
            "site", "importlib", "pkgutil", "modulefinder", "runpy", "parser", "ast", "dis",
            "pickletools", "compileall", "py_compile", "tabnanny", "pyclbr", "pydoc", "doctest",
            "bdb", "pdb", "profile", "pstats", "timeit", "trace", "tracemalloc", "encodings",
            "code", "codeop", "zipimport", "symbol", "token", "keyword", "tokenize", "symbol",
            "token", "keyword", "distutils", "ensurepip", "venv", "pip", "setuptools", "wheel"
        }
        # Also include anti-debug modules to prevent conflicts
        anti_debug_modules = {"anti_debug_injector", "anti_debug_injector_normal"}
        return module_name in stdlib_modules or module_name in anti_debug_modules

    def remap_code_in_file(self, file_path: Path):
        """
        Remap identifiers in a single file using AST transformation
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
            transformer = GlobalRenamer(self.remap_map)
            transformed_tree = transformer.visit(tree)
            ast.fix_missing_locations(transformed_tree)
            
            # Convert back to source code
            new_content = ast.unparse(transformed_tree)
            
            # Write the remapped content back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
        except Exception as e:
            print(f"Error remapping {file_path}: {e}")
    
    def add_anti_debug_protection(self, file_path: Path):
        """
        Add anti-debug and anti-injection protection to a file
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Determine which anti-debug module to use based on the setting
        if self.anti_debug == 'normal':
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
    # If the module is not available, define a dummy function
    def enable_protection():
        pass

'''

        # Check if protection is already added
        if "# Anti-debug and anti-injection protection" in content:
            return  # Already added

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(protection_code + content)


    def add_anti_debug_protection_to_entry_point(self):
        """
        Add anti-debug protection specifically to the entry point file
        """
        # The entry point file is already in the output directory
        entry_point_path = self.output_dir / self.entry_point

        # Read the current content
        with open(entry_point_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Determine which anti-debug module to use based on the setting
        if self.anti_debug == 'normal':
            module_name = 'anti_debug_injector_normal'
        else:  # Default to strict if not specified or if 'strict'
            module_name = 'anti_debug_injector'

        # Create the protection code to add at the very beginning
        protection_code = f'''# Anti-debug and anti-injection protection
try:
    from {module_name} import enable_protection
    enable_protection()
except ImportError:
    # If the module is not available, define a dummy function
    def enable_protection():
        pass

'''
        
        # Check if protection is already added
        if "# Anti-debug and anti-injection protection" in content:
            return  # Already added
        
        # Add protection at the very beginning of the file
        new_content = protection_code + content
        
        # Write the updated content back to the file
        with open(entry_point_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
    def get_python_modules(self) -> List[Path]:
        """
        Get all Python modules in the project
        """
        modules = []
        for py_file in self.output_dir.rglob("*.py"):
            # Include all Python files except the obfuscator script itself
            if py_file.name != "obfuscator.py":
                modules.append(py_file)
        return modules
    
    def add_banner_to_module(self, module_path: Path, banner: str):
        """
        Add a banner comment at the start of a module
        """
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if banner already exists
        if banner.strip() in content[:500]:  # Check first 500 chars for efficiency
            return
            
        # Add banner at the beginning, preserving any existing shebang or encoding declaration
        lines = content.split('\n')
        insert_position = 0
        
        # Skip shebang and encoding declarations
        for i, line in enumerate(lines):
            if line.startswith('#!') or line.startswith('# -*- coding:'):
                insert_position = i + 1
            else:
                break
                
        # Insert the banner
        banner_lines = [f"# {line}" for line in banner.split('\n')]
        banner_text = '\n'.join(banner_lines) + '\n\n'
        
        new_content = '\n'.join(lines[:insert_position]) + banner_text + '\n'.join(lines[insert_position:])
        
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    def run_obfuscation(self, banner_text: str = "Obfuscated by PyLockWare Obfuscator"):
        """
        Main method to run the obfuscation process
        """
        print(f"Starting obfuscation of project: {self.project_path}")
        print(f"Entry point: {self.entry_point}")
        print(f"Entry function: {self.entry_function}")
        print(f"Remap enabled: {self.remap}")
        print(f"Import obfuscation enabled: {self.obfuscate_imports}")

        # Validate paths
        self.validate_paths()

        # Copy project to output directory
        self.copy_project_to_output()

        # Build imports whitelist from the original project
        self.build_imports_whitelist()
        print(f"Collected {len(self.imports_whitelist)} imports for whitelist")

        # Get all modules from the output directory
        modules = self.get_python_modules()
        print(f"Found {len(modules)} modules to process in output directory")

        # Add anti-debug protection if enabled
        if self.anti_debug:
            print("Adding anti-debug and anti-injection protection...")
            # Copy the appropriate protection module(s) to the output directory
            import shutil

            if self.anti_debug == 'normal':
                # Copy the normal anti-debug module
                protection_module_path = self.output_dir / "anti_debug_injector_normal.py"
                shutil.copy("anti_debug_injector_normal.py", protection_module_path)
            elif self.anti_debug == 'strict' or self.anti_debug is True:
                # Copy the strict anti-debug module (original behavior)
                protection_module_path = self.output_dir / "anti_debug_injector.py"
                shutil.copy("anti_debug_injector.py", protection_module_path)
            else:
                # Default to strict if not specified
                protection_module_path = self.output_dir / "anti_debug_injector.py"
                shutil.copy("anti_debug_injector.py", protection_module_path)

            # Add protection to the entry point file first
            self.add_anti_debug_protection_to_entry_point()
            print(f"Added anti-debug protection to entry point: {self.entry_point}")

            # Add protection to each module
            for module in modules:
                # Don't add protection to the anti-debug modules themselves
                if module.name not in ["anti_debug_injector.py", "anti_debug_injector_normal.py"]:
                    self.add_anti_debug_protection(module)
                    print(f"Added anti-debug protection to: {module}")

        # Perform remapping if enabled
        if self.remap:
            print("Building global replacements...")
            self.build_global_replacements(self.output_dir)
            print(f"Created {len(self.remap_map)} global replacements")

            print("Performing remapping on all modules...")
            for module in modules:
                self.remap_code_in_file(module)
                print(f"Remapped: {module}")

        # Perform import obfuscation if enabled (after remapping to avoid conflicts with renamed identifiers)
        if self.obfuscate_imports:
            print("Obfuscating imports in all modules...")
            for module in modules:
                # Don't obfuscate the anti-debug modules themselves
                if module.name not in ["anti_debug_injector.py", "anti_debug_injector_normal.py"]:
                    with open(module, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    obfuscated_content = obfuscate_imports(content)
                    if obfuscated_content:
                        with open(module, 'w', encoding='utf-8') as f:
                            f.write(obfuscated_content)
                        print(f"Obfuscated imports in: {module}")



        # Add banner to each module
        for module in modules:
            self.add_banner_to_module(module, banner_text)
            print(f"Added banner to: {module}")

        print(f"Obfuscation process completed! Output saved to: {self.output_dir}")
    
    def copy_project_to_output(self):
        """
        Copy the entire project to the output directory
        """
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        
        shutil.copytree(self.project_path, self.output_dir)


def main():
    parser = argparse.ArgumentParser(description="Simple Python Obfuscator")
    parser.add_argument("project_path", help="Path to the project to obfuscate")
    parser.add_argument("--entry-point", required=True, help="Entry point file of the project (e.g., main.py)")
    parser.add_argument("--entry-function", default="main", help="Main function name in the entry point (default: main)")
    parser.add_argument("--banner", default="Obfuscated by PyLockWare Obfuscator", help="Banner text to add to modules")
    parser.add_argument("--output-dir", default="dist", help="Output directory for obfuscated project (default: dist)")
    parser.add_argument("--remap", action="store_true", help="Enable renaming of functions, variables, etc. to random names")
    parser.add_argument("--obfuscate-imports", action="store_true", help="Enable obfuscation of import statements")
    parser.add_argument("--anti-debug", choices=['normal', 'strict'], help="Enable anti-debug and anti-injection protection ('normal' without thread checking, 'strict' with thread checking)")


    args = parser.parse_args()

    obfuscator = PyObfuscator(
        project_path=args.project_path,
        entry_point=args.entry_point,
        entry_function=args.entry_function,
        output_dir=args.output_dir,
        remap=args.remap,
        anti_debug=args.anti_debug,
        obfuscate_imports=args.obfuscate_imports,
    )

    obfuscator.run_obfuscation(args.banner)


if __name__ == "__main__":
    main()