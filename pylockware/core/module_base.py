"""
Abstract base class for PyLockWare modules
Defines the interface that all modules must implement
"""
import abc
from pathlib import Path
from typing import Dict, Any, Optional


class ModuleBase(abc.ABC):
    """
    Abstract base class for all PyLockWare modules
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the module with optional configuration
        
        Args:
            config: Optional dictionary containing module-specific configuration
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        
    @abc.abstractmethod
    def process(self, project_path: Path, output_path: Path) -> bool:
        """
        Process the project with this module's functionality
        
        Args:
            project_path: Path to the original project
            output_path: Path to the output directory
            
        Returns:
            True if processing was successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def validate_config(self) -> bool:
        """
        Validate the module's configuration
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this module
        
        Returns:
            Dictionary containing module information
        """
        return {
            'name': self.name,
            'description': self.__doc__ or 'No description provided',
            'config': self.config
        }
    
    def set_config(self, config: Dict[str, Any]):
        """
        Update the module's configuration
        
        Args:
            config: Dictionary containing new configuration values
        """
        self.config.update(config)