"""
State Machine Module for PyLockWare
Transforms functions into state machines to obfuscate control flow
"""
from pathlib import Path
from typing import Dict, Any
from pylockware.core.module_base import ModuleBase
from pylockware.transforms.state_machine_transformer import StateMachineTransformer


class StateMachineModule(ModuleBase):
    """
    Module that transforms functions into state machines to obfuscate control flow
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

    def process(self, project_path: Path, output_path: Path) -> bool:
        """
        Process the project by transforming functions into state machines

        Args:
            project_path: Path to the original project
            output_path: Path to the output directory

        Returns:
            True if processing was successful, False otherwise
        """
        try:
            print("Applying state machine transformation to all Python files...")

            # Create an instance of the state machine transformer
            transformer = StateMachineTransformer()

            # Find all Python files in the output directory
            for py_file in output_path.rglob("*.py"):
                # Skip the obfuscator script itself and other special files
                if py_file.name not in ["obfuscator.py", "state_machine_transformer.py"]:
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            original_code = f.read()

                        # Apply state machine transformation
                        transformed_code = transformer.apply_transformation(original_code)

                        # Only write if changes were made
                        if transformed_code != original_code:
                            with open(py_file, 'w', encoding='utf-8') as f:
                                f.write(transformed_code)

                            print(f"Applied state machine transformation to {py_file}")

                    except Exception as e:
                        print(f"Error applying state machine transformation to {py_file}: {e}")

            return True
        except Exception as e:
            print(f"Error during state machine transformation: {e}")
            return False

    def validate_config(self) -> bool:
        """
        Validate the module's configuration

        Returns:
            True if configuration is valid, False otherwise
        """
        # State machine module doesn't have specific validation requirements
        return True