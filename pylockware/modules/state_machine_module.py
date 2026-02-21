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
        self.name_gen_settings = self.config.get('name_gen', 'english')
        self.entry_point = self.config.get('entry_point', None)
        self.add_junk_states = self.config.get('add_junk_states', True)

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

            # Determine the entry point file name if specified
            entry_point_filename = None
            if self.entry_point:
                entry_point_path = Path(self.entry_point)
                entry_point_filename = entry_point_path.name
                print(f"Entry point file: {entry_point_filename}")

            # Create an instance of the state machine transformer with name generator settings
            transformer = StateMachineTransformer(
                name_gen_settings=self.name_gen_settings,
                add_junk_states=self.add_junk_states
            )

            # Find all Python files in the output directory
            for py_file in output_path.rglob("*.py"):
                # Skip the obfuscator script itself and other special files
                if py_file.name not in ["obfuscator.py", "state_machine_transformer.py"]:
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            original_code = f.read()

                        # Check if this is the entry point file
                        is_entry_point = (entry_point_filename and py_file.name == entry_point_filename)
                        if is_entry_point:
                            print(f"[ENTRY POINT] Processing entry point file: {py_file}")
                            print(f"[ENTRY POINT] Original code length: {len(original_code)} chars")

                        # Apply state machine transformation
                        transformed_code = transformer.apply_transformation(original_code)

                        if is_entry_point:
                            print(f"[ENTRY POINT] Transformed code length: {len(transformed_code)} chars")
                            print(f"[ENTRY POINT] Code changed: {transformed_code != original_code}")

                        # Only write if changes were made
                        if transformed_code != original_code:
                            with open(py_file, 'w', encoding='utf-8') as f:
                                f.write(transformed_code)

                            if is_entry_point:
                                print(f"[ENTRY POINT] Successfully applied state machine transformation!")
                            else:
                                print(f"Applied state machine transformation to {py_file}")
                        else:
                            if is_entry_point:
                                print(f"[ENTRY POINT] WARNING: No changes made to entry point file!")
                                print(f"[ENTRY POINT] This may be because functions are too simple or have only 1 block")

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