"""
GUI for the Python Obfuscator using PySide6
"""
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLineEdit, QLabel, QFileDialog, QCheckBox, 
                               QTextEdit, QGroupBox, QFormLayout, QMessageBox, QComboBox,
                               QTabWidget, QScrollArea, QRadioButton)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from pylockware.core.obfuscator import PyObfuscator
from pylockware.modules.import_obf_module import ImportObfuscateModule
from pylockware.modules.nuitka_builder_module import NuitkaBuilderModule


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

        # Nuitka EXE Packaging Tab
        self.nuitka_tab = self.create_nuitka_tab()
        self.tab_widget.addTab(self.nuitka_tab, "Nuitka EXE")

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
        self.anti_debug_checkbox.clicked.connect(self.on_anti_debug_clicked)
        layout.addWidget(self.anti_debug_checkbox)
        
        # Anti-debug mode selection
        anti_debug_mode_layout = QHBoxLayout()
        anti_debug_mode_label = QLabel("Protection Level:")
        self.anti_debug_combo = QComboBox()
        self.anti_debug_combo.addItems([
            "Strict (with thread checking, breaks pyside, pyqt, numpy and most of other native libs)",
            "Normal (without thread checking)",
            "Native (high-performance protection using native DLL implementation)"
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
        self.import_obf_checkbox.clicked.connect(self.on_importobf_clicked)
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

        # Builtin dispatcher obfuscation option
        self.builtin_dispatcher_checkbox = QCheckBox("Enable builtin dispatcher obfuscation to replace built-in calls with dispatcher calls")
        layout.addWidget(self.builtin_dispatcher_checkbox)

        # Description for builtin dispatcher obfuscation
        builtin_dispatcher_desc = QLabel("Builtin dispatcher replaces built-in function calls (print(), len(), etc.) with calls\nvia a dispatcher class, making it harder to identify built-in function usage.")
        builtin_dispatcher_desc.setWordWrap(True)
        builtin_dispatcher_desc.setStyleSheet("color: gray;")
        layout.addWidget(builtin_dispatcher_desc)

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

        # Name generator settings
        name_gen_layout = QHBoxLayout()
        name_gen_label = QLabel("Name generator:")
        self.name_gen_combo = QComboBox()
        self.name_gen_combo.addItems([
            "English letters and digits",
            "Chinese characters",
            "Mixed (English + Chinese)",
            "Numbers only",
            "Hexadecimal"
        ])
        self.name_gen_combo.setCurrentIndex(0)  # Default to English
        name_gen_layout.addWidget(name_gen_label)
        name_gen_layout.addWidget(self.name_gen_combo)
        layout.addLayout(name_gen_layout)

        # Description for name generator
        name_gen_desc = QLabel("Character set used for generating random names during obfuscation.")
        name_gen_desc.setWordWrap(True)
        name_gen_desc.setStyleSheet("color: gray;")
        layout.addWidget(name_gen_desc)
        
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
        from PySide6.QtWidgets import QMessageBox
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
            'builtin_dispatcher': self.builtin_dispatcher_checkbox.isChecked(),
            'name_gen': self._get_name_gen_setting(),
        }

        # Set anti-debug option
        if self.anti_debug_checkbox.isChecked():
            import platform
            import sys
            # Check if running on Windows AMD64
            if not (sys.platform == 'win32' and platform.machine().lower() in ['amd64', 'x86_64']):
                # Show warning and disable anti-debug
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Platform Warning",
                                    "Anti-debug protection is only available for Windows AMD64. Option will be disabled.")
                params['anti_debug'] = None
            else:
                anti_debug_choice = self.anti_debug_combo.currentText()
                if "Normal" in anti_debug_choice:
                    params['anti_debug'] = 'normal'
                elif "Native" in anti_debug_choice:
                    params['anti_debug'] = 'native'
                else:  # Strict
                    params['anti_debug'] = 'strict'
        else:
            params['anti_debug'] = None

        # Set Nuitka options
        params['enable_nuitka'] = self.nuitka_enable_checkbox.isChecked()
        params['nuitka_onefile'] = self.nuitka_onefile_checkbox.isChecked()
        params['nuitka_standalone'] = self.nuitka_standalone_checkbox.isChecked()
        params['nuitka_output_name'] = self.nuitka_output_name_edit.text().strip() or None
        params['nuitka_disable_console'] = self.nuitka_disable_console_checkbox.isChecked()
        params['nuitka_icon'] = self.nuitka_icon_edit.text().strip() or None
        params['nuitka_admin'] = self.nuitka_admin_checkbox.isChecked()

        # Collect selected plugins
        nuitka_plugins = []
        if self.nuitka_plugin_tkinter.isChecked():
            nuitka_plugins.append('tk-inter')
        if self.nuitka_plugin_pyside6.isChecked():
            nuitka_plugins.append('pyside6')
        if self.nuitka_plugin_pyqt5.isChecked():
            nuitka_plugins.append('pyqt5')
        if self.nuitka_plugin_numpy.isChecked():
            nuitka_plugins.append('numpy')
        if self.nuitka_plugin_multiprocessing.isChecked():
            nuitka_plugins.append('multiprocessing')
        params['nuitka_plugins'] = nuitka_plugins

        # Extra imports
        extra_imports_str = self.nuitka_extra_imports_edit.text().strip()
        params['nuitka_extra_imports'] = [x.strip() for x in extra_imports_str.split(',') if x.strip()] if extra_imports_str else []

        # Custom options
        custom_options_str = self.nuitka_custom_options_edit.text().strip()
        params['nuitka_options'] = custom_options_str.split() if custom_options_str else []

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

    def on_nuitka_clicked(self, checked):
        """Handle Nuitka checkbox click - warn about incompatible options"""
        if checked:  # Checkbox was just checked
            # Warn about import obfuscation incompatibility and disable it
            if self.import_obf_checkbox.isChecked():
                QMessageBox.warning(
                    self, "Nuitka Compatibility Warning",
                    "Import obfuscation is incompatible with Nuitka EXE packaging.\n\n"
                    "Import obfuscation has been disabled."
                )
                self.import_obf_checkbox.setChecked(False)

    def on_importobf_clicked(self, checked):
        """Handle import obfuscation checkbox click - warn if Nuitka is enabled"""
        if checked and self.nuitka_enable_checkbox.isChecked():
            QMessageBox.warning(
                self, "Nuitka Compatibility Warning",
                "Import obfuscation is incompatible with Nuitka EXE packaging.\n\n"
                "Import obfuscation has been disabled."
            )
            self.import_obf_checkbox.setChecked(False)

    def on_anti_debug_clicked(self, checked):
        """Handle anti-debug checkbox click - warn if Nuitka is enabled"""
        if checked:
            QMessageBox.warning(
                self, "Anti-Debug Protection Warning",
                "Anti-debug protection is not a complete security solution.\n\n"
                "• It may be incompatible with other obfuscation modules\n"
                "• It can be bypassed by experienced reverse engineers\n"
                "• For production protection, use dedicated protectors like\n"
                "  Themida, VMProtect after obfuscation.\n\n"
                "Are you sure you want to enable anti-debug protection?"
            )
    
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

    def _get_name_gen_setting(self):
        """Get the selected name generator setting from the combo box."""
        index = self.name_gen_combo.currentIndex()
        name_gen_options = ['english', 'chinese', 'mixed', 'numbers', 'hex']
        return name_gen_options[index] if 0 <= index < len(name_gen_options) else 'english'

    def select_icon_file(self):
        """Open a dialog to select the icon file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon File",
            os.path.expanduser("~"),
            "Icon Files (*.ico);;All Files (*)"
        )
        if file_path:
            self.nuitka_icon_edit.setText(file_path)

    def auto_detect_plugins(self):
        """Auto-detect required plugins based on project imports"""
        project_path = self.project_path_edit.text().strip()
        if not project_path:
            QMessageBox.warning(self, "Input Error", "Please select a project path first.")
            return

        # Create an analyzer and detect frameworks
        analyzer = NuitkaBuilderModule().import_analyzer
        all_imports = analyzer.analyze_directory(Path(project_path))
        frameworks = analyzer.detect_frameworks(all_imports)

        # Update checkboxes based on detected frameworks
        self.nuitka_plugin_tkinter.setChecked(frameworks.get('tkinter', False))
        self.nuitka_plugin_pyside6.setChecked(frameworks.get('pyside6', False))
        self.nuitka_plugin_pyqt5.setChecked(frameworks.get('pyqt5', False))
        self.nuitka_plugin_numpy.setChecked(frameworks.get('numpy', False))
        self.nuitka_plugin_multiprocessing.setChecked(frameworks.get('multiprocessing', False))

        detected = [k for k, v in frameworks.items() if v]
        if detected:
            self.log_text.append(f"Auto-detected frameworks: {', '.join(detected)}")
        else:
            self.log_text.append("No specific frameworks detected")

    def create_nuitka_tab(self):
        """Create the Nuitka EXE packaging tab"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)

        # Enable Nuitka checkbox
        self.nuitka_enable_checkbox = QCheckBox("Enable EXE packaging with Nuitka")
        self.nuitka_enable_checkbox.clicked.connect(self.on_nuitka_clicked)
        layout.addWidget(self.nuitka_enable_checkbox)

        # Description
        nuitka_desc = QLabel("Nuitka compiles Python code to C/C++ and packages it into a standalone executable.\nThis makes reverse engineering significantly harder.")
        nuitka_desc.setWordWrap(True)
        nuitka_desc.setStyleSheet("color: gray;")
        layout.addWidget(nuitka_desc)

        # Output name
        output_name_layout = QHBoxLayout()
        output_name_label = QLabel("Output EXE name:")
        self.nuitka_output_name_edit = QLineEdit()
        self.nuitka_output_name_edit.setPlaceholderText("e.g., MyApplication.exe (optional)")
        output_name_layout.addWidget(output_name_label)
        output_name_layout.addWidget(self.nuitka_output_name_edit)
        layout.addLayout(output_name_layout)

        # Build mode options (both can be enabled)
        build_mode_group = QGroupBox("Build Mode")
        build_mode_layout = QVBoxLayout()

        self.nuitka_onefile_checkbox = QCheckBox("--onefile (create single executable file)")
        self.nuitka_onefile_checkbox.setChecked(True)
        build_mode_layout.addWidget(self.nuitka_onefile_checkbox)

        self.nuitka_standalone_checkbox = QCheckBox("--standalone (create standalone distribution)")
        self.nuitka_standalone_checkbox.setChecked(True)
        build_mode_layout.addWidget(self.nuitka_standalone_checkbox)

        build_mode_desc = QLabel("Note: Both options can be enabled together. --onefile creates a single .exe,\n--standalone ensures all dependencies are included.")
        build_mode_desc.setWordWrap(True)
        build_mode_desc.setStyleSheet("color: gray;")
        build_mode_layout.addWidget(build_mode_desc)

        build_mode_group.setLayout(build_mode_layout)
        layout.addWidget(build_mode_group)

        # Windows options
        windows_group = QGroupBox("Windows Options")
        windows_layout = QVBoxLayout()

        self.nuitka_disable_console_checkbox = QCheckBox("Disable console window (GUI applications)")
        self.nuitka_disable_console_checkbox.setChecked(True)
        windows_layout.addWidget(self.nuitka_disable_console_checkbox)

        self.nuitka_admin_checkbox = QCheckBox("Request administrator privileges (UAC)")
        windows_layout.addWidget(self.nuitka_admin_checkbox)

        # Icon file
        icon_layout = QHBoxLayout()
        icon_label = QLabel("Icon file (.ico):")
        self.nuitka_icon_edit = QLineEdit()
        self.nuitka_icon_edit.setPlaceholderText("Path to .ico file (optional)")
        icon_browse_btn = QPushButton("Browse...")
        icon_browse_btn.clicked.connect(self.select_icon_file)
        icon_layout.addWidget(icon_label)
        icon_layout.addWidget(self.nuitka_icon_edit)
        icon_layout.addWidget(icon_browse_btn)
        windows_layout.addLayout(icon_layout)

        windows_group.setLayout(windows_layout)
        layout.addWidget(windows_group)

        # Plugins selection
        plugins_group = QGroupBox("Nuitka Plugins")
        plugins_layout = QVBoxLayout()

        self.nuitka_plugin_tkinter = QCheckBox("tk-inter (Tkinter GUI)")
        plugins_layout.addWidget(self.nuitka_plugin_tkinter)

        self.nuitka_plugin_pyside6 = QCheckBox("pyside6 (PySide6 GUI)")
        plugins_layout.addWidget(self.nuitka_plugin_pyside6)

        self.nuitka_plugin_pyqt5 = QCheckBox("pyqt5 (PyQt5 GUI)")
        plugins_layout.addWidget(self.nuitka_plugin_pyqt5)

        self.nuitka_plugin_numpy = QCheckBox("numpy (NumPy support)")
        plugins_layout.addWidget(self.nuitka_plugin_numpy)

        self.nuitka_plugin_multiprocessing = QCheckBox("multiprocessing")
        plugins_layout.addWidget(self.nuitka_plugin_multiprocessing)

        # Auto-detect button
        auto_detect_btn = QPushButton("Auto-detect required plugins")
        auto_detect_btn.clicked.connect(self.auto_detect_plugins)
        plugins_layout.addWidget(auto_detect_btn)

        plugins_group.setLayout(plugins_layout)
        layout.addWidget(plugins_group)

        # Extra imports
        extra_imports_layout = QVBoxLayout()
        extra_imports_label = QLabel("Extra imports (comma-separated):")
        self.nuitka_extra_imports_edit = QLineEdit()
        self.nuitka_extra_imports_edit.setPlaceholderText("e.g., requests, PIL, custom_module")
        extra_imports_layout.addWidget(extra_imports_label)
        extra_imports_layout.addWidget(self.nuitka_extra_imports_edit)
        layout.addLayout(extra_imports_layout)

        # Custom options
        custom_options_layout = QVBoxLayout()
        custom_options_label = QLabel("Custom Nuitka options (space-separated):")
        self.nuitka_custom_options_edit = QLineEdit()
        self.nuitka_custom_options_edit.setPlaceholderText("e.g., --nofollow-imports --assume-yes-for-downloads")
        custom_options_layout.addWidget(custom_options_label)
        custom_options_layout.addWidget(self.nuitka_custom_options_edit)
        layout.addLayout(custom_options_layout)

        # Warning note
        warning_note = QLabel("Note: Nuitka must be installed separately: pip install nuitka")
        warning_note.setWordWrap(True)
        warning_note.setStyleSheet("color: orange;")
        layout.addWidget(warning_note)

        layout.addStretch()
        scroll.setWidget(scroll_content)

        nuitka_main_layout = QVBoxLayout(tab)
        nuitka_main_layout.addWidget(scroll)

        return tab


def main():
    app = QApplication(sys.argv)
    window = ObfuscatorGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()