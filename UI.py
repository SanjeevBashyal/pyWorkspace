import sys
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from pyworkspace.sheets import (
    save_session_to_sheets,
    load_session_from_sheets,
    list_workspaces_from_sheets,
    delete_workspace_from_sheets
)


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyWorkspace Manager")
        self.setMinimumWidth(420)


        # Main Widget and Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 1. Save Workspace Group
        save_group = QGroupBox("Save/Replace Current Desktop")
        save_layout = QVBoxLayout(save_group)
        
        self.save_combo = QComboBox()
        self.save_combo.addItem("")
        self.save_combo.addItem("Add New...")
        self.save_combo.currentIndexChanged.connect(self.on_save_combo_changed)
        save_layout.addWidget(self.save_combo)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter new workspace name (e.g. Coding)")
        self.name_input.hide() # Hidden by default
        save_layout.addWidget(self.name_input)
        
        self.save_btn = QPushButton("Save Workspace")
        self.save_btn.clicked.connect(self.on_save_clicked)
        save_layout.addWidget(self.save_btn)
        
        main_layout.addWidget(save_group)

        # 2. Resume Workspace Group
        resume_group = QGroupBox("Resume Workspace")
        resume_layout = QVBoxLayout(resume_group)
        
        self.resume_combo = QComboBox()
        resume_layout.addWidget(self.resume_combo)
        
        resume_btn_layout = QHBoxLayout()
        self.resume_btn = QPushButton("Resume Selected")
        self.resume_btn.clicked.connect(self.on_resume_clicked)
        self.refresh_btn = QPushButton("Refresh List")
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        
        # Delete button with error styling
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet("background-color: #c23616; color: white;")
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        
        resume_btn_layout.addWidget(self.resume_btn)
        resume_btn_layout.addWidget(self.refresh_btn)
        resume_btn_layout.addWidget(self.delete_btn)
        resume_layout.addLayout(resume_btn_layout)
        
        main_layout.addWidget(resume_group)

        # 3. Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self.status_label)

        # Initialize Signals
        self.signals = WorkerSignals()
        self.signals.result.connect(self.on_workspaces_loaded)
        self.signals.finished.connect(self.on_action_finished)
        self.signals.error.connect(self.on_action_error)

        # Load initial workspaces
        self.on_refresh_clicked()

        self.apply_styles()

    def apply_styles(self):
        style = """
        QMainWindow { background-color: #f7f9fc; }
        QGroupBox { font-weight: bold; padding-top: 15px; border: 1px solid #dcdde1; border-radius: 5px; margin-top: 10px; }
        QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px; color: #2f3640; }
        QLineEdit, QComboBox { padding: 8px; border: 1px solid #dcdde1; border-radius: 4px; background-color: white; }
        QPushButton { padding: 8px; background-color: #0097e6; color: white; border: none; border-radius: 4px; font-weight: bold; }
        QPushButton:hover { background-color: #00a8ff; }
        QPushButton:disabled { background-color: #bdc3c7; }
        """
        self.setStyleSheet(style)

    def set_loading_state(self, message: str, is_loading: bool):
        self.status_label.setText(message)
        self.save_btn.setEnabled(not is_loading)
        self.resume_btn.setEnabled(not is_loading)
        self.refresh_btn.setEnabled(not is_loading)
        self.delete_btn.setEnabled(not is_loading)
        self.save_combo.setEnabled(not is_loading)
        self.resume_combo.setEnabled(not is_loading)
        self.name_input.setEnabled(not is_loading)
        if is_loading:
            self.status_label.setStyleSheet("color: #e1b12c; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: #44bd32; font-weight: bold;")

    def on_save_combo_changed(self):
        if self.save_combo.currentText() == "Add New...":
            self.name_input.show()
        else:
            self.name_input.hide()
            
        # Optional: gracefully shrink the window back down if it was expanded
        self.adjustSize()

    def on_refresh_clicked(self):
        self.set_loading_state("Fetching workspaces from Google Sheets...", True)
        
        def fetch():
            try:
                names = list_workspaces_from_sheets()
                self.signals.result.emit(names)
            except Exception as e:
                self.signals.error.emit(str(e))
                
        threading.Thread(target=fetch, daemon=True).start()

    def on_workspaces_loaded(self, names):
        # We block signals temporarily so clearing doesn't trigger unexpected events
        self.save_combo.blockSignals(True)
        self.resume_combo.blockSignals(True)
        
        # Remember user's selection
        current_save = self.save_combo.currentText()
        current_resume = self.resume_combo.currentText()
        
        self.save_combo.clear()
        self.save_combo.addItem("")
        self.save_combo.addItem("Add New...")
        
        self.resume_combo.clear()

        if names:
            self.save_combo.addItems(names)
            self.resume_combo.addItems(names)
            self.set_loading_state(f"Loaded {len(names)} workspaces.", False)
        else:
            self.resume_combo.addItem("No workspaces found")
            self.set_loading_state("No workspaces found in Master sheet.", False)

        # Restore user's selection if it still exists
        if current_save in names or current_save in ["", "Add New..."]:
            self.save_combo.setCurrentText(current_save)
            
        if current_resume in names:
            self.resume_combo.setCurrentText(current_resume)
        elif names:
            self.resume_combo.setCurrentIndex(0)

        # Unblock and trigger visibility update for text input
        self.save_combo.blockSignals(False)
        self.resume_combo.blockSignals(False)
        self.on_save_combo_changed()

    def on_save_clicked(self):
        choice = self.save_combo.currentText()
        
        if choice == "Add New...":
            name = self.name_input.text().strip()
            if not name:
                QMessageBox.warning(self, "Input Error", "Please enter a new workspace name.")
                return
        elif choice == "":
            QMessageBox.warning(self, "Input Error", "Please select a workspace to replace or 'Add New...'.")
            return
        else:
            name = choice
            # Ask for confirmation before replacing an existing workspace
            reply = QMessageBox.question(
                self, 'Confirm Replace',
                f"Are you sure you want to replace '{name}' with the current desktop state?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.set_loading_state(f"Saving workspace '{name}'...", True)

        def save():
            try:
                success = save_session_to_sheets(name)
                if success:
                    # After a successful save, refresh the lists automatically so it appears!
                    names = list_workspaces_from_sheets()
                    self.signals.result.emit(names)
                    self.signals.finished.emit()
                else:
                    self.signals.error.emit("Failed to save workspace.")
            except Exception as e:
                self.signals.error.emit(str(e))

        threading.Thread(target=save, daemon=True).start()

    def on_resume_clicked(self):
        name = self.resume_combo.currentText()
        if not name or name == "No workspaces found":
            QMessageBox.warning(self, "Selection Error", "Please select a valid workspace to resume.")
            return

        self.set_loading_state(f"Loading workspace '{name}'...", True)

        def resume():
            try:
                success = load_session_from_sheets(name)
                if success:
                    self.signals.finished.emit()
                else:
                    self.signals.error.emit("Failed to load workspace.")
            except Exception as e:
                self.signals.error.emit(str(e))

        threading.Thread(target=resume, daemon=True).start()

    def on_delete_clicked(self):
        name = self.resume_combo.currentText()
        if not name or name == "No workspaces found":
            QMessageBox.warning(self, "Selection Error", "Please select a valid workspace to delete.")
            return

        reply = QMessageBox.warning(
            self, 'Confirm Delete',
            f"Are you sure you want to PERMANENTLY delete the workspace '{name}'?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        self.set_loading_state(f"Deleting workspace '{name}'...", True)

        def delete():
            try:
                success = delete_workspace_from_sheets(name)
                if success:
                    # Refresh the lists automatically after successful deletion
                    names = list_workspaces_from_sheets()
                    self.signals.result.emit(names)
                    self.signals.finished.emit()
                else:
                    self.signals.error.emit("Failed to delete workspace.")
            except Exception as e:
                self.signals.error.emit(str(e))

        threading.Thread(target=delete, daemon=True).start()

    def on_action_finished(self):
        self.set_loading_state("Action completed successfully!", False)
        # Clear the text input upon successful save context
        self.name_input.clear()
        
        # After saving a new item, we might want to reset the save combo back to empty
        # to prevent accidental overrides, but it's optional. Let's reset it to blank.
        if self.save_combo.currentText() == "Add New...":
            self.save_combo.setCurrentIndex(0)

    def on_action_error(self, error_msg):
        self.set_loading_state("Error occurred.", False)
        self.status_label.setStyleSheet("color: #c23616; font-weight: bold;")
        QMessageBox.critical(self, "Error", error_msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec())
