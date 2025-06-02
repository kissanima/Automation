"""
Login Dialog - Facebook Authentication Interface
Secure login form with 2FA support
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QCheckBox, QMessageBox,
                             QProgressBar, QGroupBox, QFormLayout, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QIcon

class LoginWorker(QThread):
    """Worker thread for Facebook login to prevent UI freezing"""
    login_complete = pyqtSignal(bool, str)
    login_progress = pyqtSignal(str)  # For status updates
    
    def __init__(self, facebook_login, username, password):
        super().__init__()
        self.facebook_login = facebook_login
        self.username = username
        self.password = password
    
    def run(self):
        """Perform login in background thread"""
        try:
            self.login_progress.emit("Connecting to Facebook...")
            success = self.facebook_login.login(self.username, self.password)
            if success:
                self.login_complete.emit(True, "Login successful!")
            else:
                self.login_complete.emit(False, "Login failed. Please check your credentials or complete 2FA if prompted.")
        except Exception as e:
            self.login_complete.emit(False, f"Login error: {str(e)}")

class LoginDialog(QDialog):
    def __init__(self, facebook_login, parent=None):
        super().__init__(parent)
        self.facebook_login = facebook_login
        self.login_worker = None
        self.init_ui()
        self.load_saved_credentials()
    
    def init_ui(self):
        """Initialize login dialog UI"""
        self.setWindowTitle("Facebook Login")
        self.setFixedSize(450, 400)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_label = QLabel("🔐 Facebook Login")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(header_label)
        
        # Warning message
        warning_label = QLabel("⚠️ Your credentials are encrypted and stored securely")
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(warning_label)
        
        # 2FA info
        twofa_label = QLabel("📱 If 2FA is enabled, approve the login on your mobile device")
        twofa_label.setAlignment(Qt.AlignCenter)
        twofa_label.setStyleSheet("color: #4267B2; margin-bottom: 10px; font-weight: bold;")
        layout.addWidget(twofa_label)
        
        # Login form group
        form_group = QGroupBox("Credentials")
        form_layout = QFormLayout()
        form_group.setLayout(form_layout)
        
        # Username field
        self.username_field = QLineEdit()
        self.username_field.setPlaceholderText("Email or phone number")
        self.username_field.textChanged.connect(self.validate_form)
        form_layout.addRow("Username:", self.username_field)
        
        # Password field
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)
        self.password_field.setPlaceholderText("Password")
        self.password_field.textChanged.connect(self.validate_form)
        self.password_field.returnPressed.connect(self.login)
        form_layout.addRow("Password:", self.password_field)
        
        # Remember credentials checkbox
        self.remember_checkbox = QCheckBox("Remember credentials")
        self.remember_checkbox.setChecked(True)
        form_layout.addWidget(self.remember_checkbox)
        
        layout.addWidget(form_group)
        
        # Status area
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        status_group.setLayout(status_layout)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        self.status_text.setPlaceholderText("Ready to login...")
        status_layout.addWidget(self.status_text)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.login_button = QPushButton("Login")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.login)
        self.login_button.setEnabled(False)
        button_layout.addWidget(self.login_button)
        
        layout.addLayout(button_layout)
        
        # Style the dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4267B2;
            }
            QPushButton {
                background-color: #4267B2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #365899;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
        """)
    
    def load_saved_credentials(self):
        """Load saved credentials if available"""
        try:
            username, password = self.facebook_login.load_credentials()
            if username and password:
                self.username_field.setText(username)
                self.password_field.setText(password)
                self.remember_checkbox.setChecked(True)
        except Exception:
            pass  # No saved credentials
    
    def validate_form(self):
        """Enable/disable login button based on form validation"""
        username = self.username_field.text().strip()
        password = self.password_field.text().strip()
        
        is_valid = len(username) > 0 and len(password) > 0
        self.login_button.setEnabled(is_valid)
    
    def login(self):
        """Perform Facebook login"""
        username = self.username_field.text().strip()
        password = self.password_field.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Invalid Input", 
                              "Please enter both username and password.")
            return
        
        # Update status
        self.status_text.setPlainText("Starting login process...\n")
        self.status_text.append("📱 If you have 2FA enabled, please check your mobile device for approval notification.")
        
        # Disable UI during login
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        
        # Start login in background thread
        self.login_worker = LoginWorker(self.facebook_login, username, password)
        self.login_worker.login_complete.connect(self.on_login_complete)
        self.login_worker.login_progress.connect(self.on_login_progress)
        self.login_worker.start()
    
    def on_login_progress(self, message):
        """Update login progress"""
        self.status_text.append(f"• {message}")
    
    def on_login_complete(self, success, message):
        """Handle login completion"""
        self.progress_bar.setVisible(False)
        self.set_ui_enabled(True)
        
        if success:
            # Save credentials if requested
            if self.remember_checkbox.isChecked():
                try:
                    self.facebook_login.save_credentials(
                        self.username_field.text().strip(),
                        self.password_field.text().strip()
                    )
                except Exception as e:
                    print(f"Failed to save credentials: {e}")
            
            self.status_text.append(f"✅ {message}")
            QMessageBox.information(self, "Login Successful", message)
            self.accept()
        else:
            self.status_text.append(f"❌ {message}")
            QMessageBox.critical(self, "Login Failed", message)
            self.password_field.clear()
            self.password_field.setFocus()
    
    def set_ui_enabled(self, enabled):
        """Enable/disable UI elements"""
        # Fix: Ensure enabled is boolean
        enabled = bool(enabled)
        
        self.username_field.setEnabled(enabled)
        self.password_field.setEnabled(enabled)
        self.remember_checkbox.setEnabled(enabled)
        
        # Fix: Properly check if fields have content when enabling
        if enabled:
            username_text = self.username_field.text().strip()
            password_text = self.password_field.text().strip()
            self.login_button.setEnabled(bool(username_text and password_text))
        else:
            self.login_button.setEnabled(False)
        
        self.cancel_button.setEnabled(enabled)
    
    def reject(self):
        """Handle dialog cancellation"""
        if self.login_worker and self.login_worker.isRunning():
            self.login_worker.terminate()
        super().reject()
