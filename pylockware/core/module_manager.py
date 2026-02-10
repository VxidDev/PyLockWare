"""
Module Manager for PyLockWare
Manages the execution of multiple obfuscation modules
"""
import shutil
from pathlib import Path
from typing import List, Dict, Any
from pylockware.core.module_base import ModuleBase


class ModuleManager:
    """
    Manages the execution of multiple obfuscation modules
    """
    
    def __init__(self):
        self.modules: List[ModuleBase] = []
        self.project_path = None
        self.output_path = None
        
    def add_module(self, module: ModuleBase):
        """
        Add a module to the manager
        
        Args:
            module: An instance of a ModuleBase subclass
        """
        if not isinstance(module, ModuleBase):
            raise TypeError("Module must inherit from ModuleBase")
        self.modules.append(module)
        
    def remove_module(self, module_name: str):
        """
        Remove a module by name
        
        Args:
            module_name: Name of the module to remove
        """
        self.modules = [m for m in self.modules if m.name != module_name]
        
    def set_project_paths(self, project_path: Path, output_path: Path):
        """
        Set the project paths for processing
        
        Args:
            project_path: Path to the original project
            output_path: Path to the output directory
        """
        self.project_path = Path(project_path)
        self.output_path = Path(output_path)
        
    def copy_project_to_output(self):
        """
        Copy the entire project to the output directory
        """
        if self.output_path.exists():
            shutil.rmtree(self.output_path)

        shutil.copytree(self.project_path, self.output_path)
        
    def run_modules(self) -> bool:
        """
        Run all registered modules on the project
        
        Returns:
            True if all modules executed successfully, False otherwise
        """
        if not self.project_path or not self.output_path:
            raise ValueError("Project paths not set. Call set_project_paths first.")
            
        # Copy project to output directory
        self.copy_project_to_output()
        
        # Validate all modules
        for module in self.modules:
            if not module.validate_config():
                print(f"Configuration validation failed for module: {module.name}")
                return False
                
        # Run each module
        for module in self.modules:
            print(f"Running module: {module.name}")
            success = module.process(self.project_path, self.output_path)
            if not success:
                print(f"Module {module.name} failed to process the project")
                return False
            print(f"Module {module.name} completed successfully")
                
        return True
        
    def get_module_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all registered modules
        
        Returns:
            List of dictionaries containing module information
        """
        return [module.get_info() for module in self.modules]