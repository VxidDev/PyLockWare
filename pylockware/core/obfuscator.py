"""
Updated PyLockWare Obfuscator
Uses the new modular system with abstract base classes
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

from pylockware.core.module_manager import ModuleManager
from pylockware.modules.remap_module import RemapModule
from pylockware.modules.string_protect_module import StringProtectModule
from pylockware.modules.number_obf_module import NumberObfModule
from pylockware.modules.anti_debug_module import AntiDebugModule
from pylockware.modules.import_obf_module import ImportObfuscateModule
from pylockware.modules.state_machine_module import StateMachineModule


class PyObfuscator:
    """
    A Python obfuscator using the new modular system
    """

    def __init__(self, project_path: str, entry_point: str, entry_function: str = "main", output_dir: str = "dist",
                 remap: bool = False, anti_debug: str = None, string_prot: bool = False, num_obf: bool = False,
                 import_obf: bool = False, state_machine: bool = False):
        self.project_path = Path(project_path)
        self.entry_point = Path(entry_point)
        self.entry_function = entry_function
        self.output_dir = Path(output_dir)
        self.remap = remap
        self.anti_debug = anti_debug  # Can be None, 'normal', or 'strict'
        self.string_prot = string_prot  # Enable string protection
        self.num_obf = num_obf  # Enable number obfuscation
        self.import_obf = import_obf  # Enable import obfuscation
        self.state_machine = state_machine  # Enable state machine obfuscation
        
        # Initialize module manager
        self.module_manager = ModuleManager()
        self.setup_modules()
        
    def setup_modules(self):
        """
        Setup the required modules based on configuration
        """
        # Set project paths in the module manager
        self.module_manager.set_project_paths(self.project_path, self.output_dir)

        if self.remap:
            remap_config = {'entry_function': self.entry_function}
            self.module_manager.add_module(RemapModule(remap_config))

        # Add modules based on configuration
        if self.string_prot:
            string_prot_config = {}
            self.module_manager.add_module(StringProtectModule(string_prot_config))

        # Import obfuscation should happen AFTER remapping to capture remapped names
        if self.import_obf:
            import_obf_config = {}
            self.module_manager.add_module(ImportObfuscateModule(import_obf_config))

        if self.num_obf:
            num_obf_config = {}
            self.module_manager.add_module(NumberObfModule(num_obf_config))
            

            


        if self.anti_debug:
            anti_debug_config = {
                'mode': self.anti_debug,
                'entry_point': str(self.entry_point)
            }
            self.module_manager.add_module(AntiDebugModule(anti_debug_config))

        if self.state_machine:
            state_machine_config = {}
            self.module_manager.add_module(StateMachineModule(state_machine_config))
    
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

    def run_obfuscation(self, banner_text: str = "Obfuscated by PyLockWare Obfuscator"):
        """
        Main method to run the obfuscation process using modules
        """
        print(f"Starting obfuscation of project: {self.project_path}")
        print(f"Entry point: {self.entry_point}")
        print(f"Entry function: {self.entry_function}")
        print(f"Modules enabled: remap={self.remap}, anti_debug={self.anti_debug}, string_prot={self.string_prot}, num_obf={self.num_obf}, import_obf={self.import_obf}, state_machine={self.state_machine}")

        # Validate paths
        self.validate_paths()

        # Run all modules
        success = self.module_manager.run_modules()
        
        if not success:
            print("Obfuscation failed due to module execution error")
            return False

        # Get all modules from the output directory to add banners
        modules = []
        for py_file in self.output_dir.rglob("*.py"):
            # Include all Python files except the obfuscator script itself
            if py_file.name != "obfuscator.py":
                modules.append(py_file)

        # Add banner to each module
        for module in modules:
            self.add_banner_to_module(module, banner_text)
            print(f"Added banner to: {module}")

        print(f"Obfuscation process completed! Output saved to: {self.output_dir}")
        return True

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