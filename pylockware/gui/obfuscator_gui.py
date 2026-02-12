"""
GUI for the Python Obfuscator using PySide6
"""
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLineEdit, QLabel, QFileDialog, QCheckBox, 
                               QTextEdit, QGroupBox, QFormLayout, QMessageBox, QComboBox,
                               QTabWidget, QScrollArea)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from pylockware.core.obfuscator import PyObfuscator
from pylockware.modules.import_obf_module import ImportObfuscateModule


class ObfuscatorWorker(QThread):
    """
    Worker thread for running the obfuscator to prevent GUI freezing
    """
    progress_signal = Signal(str)
    finished_signal = Signal(bool, str)  # success, message
    
    def __init__(self, obfuscator_params):
        super().__init__()
        self.obfuscator_params = obfuscator_params
        
    def run(self):
        try:
            # Create and run the obfuscator
            obfuscator = PyObfuscator(**self.obfuscator_params)
            obfuscator.run_obfuscation()
            self.finished_signal.emit(True, "Obfuscation completed successfully!")
        except Exception as e:
            self.finished_signal.emit(False, f"Error during obfuscation: {str(e)}")


class ObfuscatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyLockWare Python Obfuscator")
        self.setGeometry(100, 100, 900, 800)
        
        # Set up the central widget and tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("PyLockWare Python Obfuscator")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Project Configuration Tab
        self.project_tab = self.create_project_tab()
        self.tab_widget.addTab(self.project_tab, "Project Configuration")
        
        # Obfuscation Settings Tab
        self.obfuscation_tab = self.create_obfuscation_tab()
        self.tab_widget.addTab(self.obfuscation_tab, "Obfuscation")

        # Control Flow Obfuscation Tab
        self.control_flow_tab = self.create_control_flow_tab()
        self.tab_widget.addTab(self.control_flow_tab, "Control Flow Obf")

        # Runtime Protection Tab
        self.protection_tab = self.create_protection_tab()
        self.tab_widget.addTab(self.protection_tab, "Runtime Protection")
        
        # Additional Settings Tab
        self.additional_tab = self.create_additional_tab()
        self.tab_widget.addTab(self.additional_tab, "Additional Settings")
        
        main_layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Obfuscation")
        self.start_btn.clicked.connect(self.start_obfuscation)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(button_layout)
        
        # Log output
        log_group = QGroupBox("Log Output")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # Initialize worker
        self.worker = None
    
    def create_project_tab(self):
        """Create the project configuration tab"""
        tab = QWidget()
        layout = QFormLayout()
        
        # Project path
        project_hbox = QHBoxLayout()
        self.project_path_edit = QLineEdit()
        self.project_path_edit.setPlaceholderText("Select the project directory to obfuscate")
        project_select_btn = QPushButton("Browse...")
        project_select_btn.clicked.connect(self.select_project_path)
        project_hbox.addWidget(self.project_path_edit)
        project_hbox.addWidget(project_select_btn)
        layout.addRow("Project Path:", project_hbox)
        
        # Entry point
        self.entry_point_edit = QLineEdit()
        self.entry_point_edit.setPlaceholderText("e.g., main.py or app/main.py")
        layout.addRow("Entry Point:", self.entry_point_edit)
        
        # Entry function
        self.entry_function_edit = QLineEdit("main")
        layout.addRow("Entry Function:", self.entry_function_edit)
        
        # Output directory
        self.output_dir_edit = QLineEdit("dist")
        layout.addRow("Output Directory:", self.output_dir_edit)
        
        tab.setLayout(layout)
        return tab
    
    def create_obfuscation_tab(self):
        """Create the obfuscation settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Remap option
        self.remap_checkbox = QCheckBox("Enable renaming of functions, variables, etc. to random names")
        layout.addWidget(self.remap_checkbox)

        # Description for remapping
        remap_desc = QLabel("Remapping renames all functions, variables, classes, and other identifiers to random names,\nmaking the code harder to understand and reverse engineer.")
        remap_desc.setWordWrap(True)
        remap_desc.setStyleSheet("color: gray;")
        layout.addWidget(remap_desc)

        # String protection option
        self.string_prot_checkbox = QCheckBox("Enable string protection using base64 and zlib encoding")
        layout.addWidget(self.string_prot_checkbox)

        # Description for string protection
        string_prot_desc = QLabel("String protection encodes string literals in your code using base64 and zlib,\nmaking it harder to identify sensitive strings in your application.")
        string_prot_desc.setWordWrap(True)
        string_prot_desc.setStyleSheet("color: gray;")
        layout.addWidget(string_prot_desc)

        layout.addStretch()  # Add space to push content to the top
        tab.setLayout(layout)
        return tab
    
    def create_protection_tab(self):
        """Create the runtime protection tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Anti-debug option
        self.anti_debug_checkbox = QCheckBox("Enable anti-debug and anti-injection protection")
        layout.addWidget(self.anti_debug_checkbox)
        
        # Anti-debug mode selection
        anti_debug_mode_layout = QHBoxLayout()
        anti_debug_mode_label = QLabel("Protection Level:")
        self.anti_debug_combo = QComboBox()
        self.anti_debug_combo.addItems([
            "Strict (with thread checking, breaks pyside, pyqt, numpy and most of other native libs)",
            "Normal (without thread checking)"
        ])
        self.anti_debug_combo.setCurrentIndex(0)  # Default to strict
        self.anti_debug_combo.setEnabled(True)

        anti_debug_mode_layout.addWidget(anti_debug_mode_label)
        anti_debug_mode_layout.addWidget(self.anti_debug_combo)
        anti_debug_mode_layout.addStretch()
        layout.addLayout(anti_debug_mode_layout)
        
        # Description for anti-debug
        anti_debug_desc = QLabel("Anti-debug protection adds code to detect and prevent debugging attempts,\nmaking it harder for attackers to analyze your application.")
        anti_debug_desc.setWordWrap(True)
        anti_debug_desc.setStyleSheet("color: gray;")
        layout.addWidget(anti_debug_desc)
        
        layout.addStretch()  # Add space to push content to the top
        tab.setLayout(layout)
        return tab

    def create_control_flow_tab(self):
        """Create the control flow obfuscation tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Number obfuscation option
        self.num_obf_checkbox = QCheckBox("Enable number obfuscation using arithmetic expressions")
        layout.addWidget(self.num_obf_checkbox)

        # Description for number obfuscation
        num_obf_desc = QLabel("Number obfuscation replaces numeric literals with equivalent arithmetic expressions,\nmaking it harder to understand the meaning of numeric values in your code.")
        num_obf_desc.setWordWrap(True)
        num_obf_desc.setStyleSheet("color: gray;")
        layout.addWidget(num_obf_desc)

        # Import obfuscation option
        self.import_obf_checkbox = QCheckBox("Enable import obfuscation using dynamic execution techniques")
        layout.addWidget(self.import_obf_checkbox)

        # Description for import obfuscation
        import_obf_desc = QLabel("Import obfuscation hides import statements using dynamic execution methods\nlike __import__() and exec(), making dependencies harder to identify.")
        import_obf_desc.setWordWrap(True)
        import_obf_desc.setStyleSheet("color: gray;")
        layout.addWidget(import_obf_desc)

        # State machine obfuscation option
        self.state_machine_checkbox = QCheckBox("Enable state machine obfuscation to transform functions into state machines")
        layout.addWidget(self.state_machine_checkbox)

        # Description for state machine obfuscation
        state_machine_desc = QLabel("State machine obfuscation transforms functions into state machines,\nmaking control flow harder to analyze and understand.")
        state_machine_desc.setWordWrap(True)
        state_machine_desc.setStyleSheet("color: gray;")
        layout.addWidget(state_machine_desc)

        layout.addStretch()  # Add space to push content to the top
        tab.setLayout(layout)
        return tab

    def create_additional_tab(self):
        """Create the additional settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Banner text
        banner_layout = QHBoxLayout()
        banner_label = QLabel("Banner text:")
        self.banner_edit = QLineEdit("Obfuscated by PyLockWare Obfuscator")
        banner_layout.addWidget(banner_label)
        banner_layout.addWidget(self.banner_edit)
        layout.addLayout(banner_layout)
        
        # Description for banner
        banner_desc = QLabel("The banner text will be added to the beginning of each obfuscated Python file.")
        banner_desc.setWordWrap(True)
        banner_desc.setStyleSheet("color: gray;")
        layout.addWidget(banner_desc)
        
        layout.addStretch()  # Add space to push content to the top
        tab.setLayout(layout)
        return tab
        
    def select_project_path(self):
        """Open a dialog to select the project directory"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Project Directory", 
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if directory:
            self.project_path_edit.setText(directory)
    
    def start_obfuscation(self):
        """Start the obfuscation process"""
        # Validate inputs
        if not self.project_path_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "Please select a project path.")
            return
            
        if not self.entry_point_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "Please specify an entry point file.")
            return
        
        # Prepare parameters for the obfuscator
        params = {
            'project_path': self.project_path_edit.text().strip(),
            'entry_point': self.entry_point_edit.text().strip(),
            'entry_function': self.entry_function_edit.text().strip(),
            'output_dir': self.output_dir_edit.text().strip(),
            'remap': self.remap_checkbox.isChecked(),
            'string_prot': self.string_prot_checkbox.isChecked(),
            'num_obf': self.num_obf_checkbox.isChecked(),
            'import_obf': self.import_obf_checkbox.isChecked(),
            'state_machine': self.state_machine_checkbox.isChecked(),
        }

        # Set anti-debug option
        if self.anti_debug_checkbox.isChecked():
            anti_debug_choice = self.anti_debug_combo.currentText()
            if "Normal" in anti_debug_choice:
                params['anti_debug'] = 'normal'
            else:  # Strict
                params['anti_debug'] = 'strict'
        else:
            params['anti_debug'] = None
        
        # Disable UI during processing
        self.start_btn.setEnabled(False)
        self.log_text.clear()
        self.log_text.append("Starting obfuscation process...\n")
        
        # Create and start the worker thread
        self.worker = ObfuscatorWorker(params)
        self.worker.progress_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.obfuscation_finished)
        self.worker.start()
    
    def update_log(self, message):
        """Update the log text with a message"""
        self.log_text.append(message)
    
    def obfuscation_finished(self, success, message):
        """Handle the completion of the obfuscation process"""
        self.log_text.append(message)
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
        
        # Re-enable UI
        self.start_btn.setEnabled(True)
        
        # Clean up the worker
        self.worker = None


def main():
    app = QApplication(sys.argv)
    window = ObfuscatorGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()