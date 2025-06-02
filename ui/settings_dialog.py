"""
Settings Dialog - Comprehensive Configuration Management
Configure all automation timing, behavior, and preferences
"""

import os
import json
import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSpinBox, QCheckBox, QComboBox, QPushButton,
                             QGroupBox, QFormLayout, QTabWidget, QWidget,
                             QSlider, QMessageBox, QLineEdit, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class SettingsDialog(QDialog):
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.settings = self.load_settings()
        
        self.init_ui()
        self.load_current_settings()
    
    def init_ui(self):
        """Initialize settings dialog UI"""
        self.setWindowTitle("Automation Settings")
        self.setGeometry(250, 250, 600, 700)
        self.setModal(True)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_label = QLabel("⚙️ Automation Settings")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(header_label)
        
        # Create tabs for different setting categories
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_general_tab()
        self.create_timing_tab()
        self.create_typing_tab()
        self.create_posting_tab()
        self.create_advanced_tab()
        
        # Button panel
        button_layout = QHBoxLayout()
        
        # Reset to defaults
        reset_button = QPushButton("🔄 Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_button)
        
        button_layout.addStretch()
        
        # Cancel
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # Save
        save_button = QPushButton("💾 Save Settings")
        save_button.setDefault(True)
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        # Apply styles
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
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
            QPushButton {
                background-color: #4267B2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #365899;
            }
        """)
    
    def create_general_tab(self):
        """General application settings"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Startup Settings
        startup_group = QGroupBox("Startup Behavior")
        startup_layout = QFormLayout()
        startup_group.setLayout(startup_layout)
        
        self.auto_start_checkbox = QCheckBox("Auto-start with Windows")
        startup_layout.addRow("", self.auto_start_checkbox)
        
        self.start_minimized_checkbox = QCheckBox("Start minimized to system tray")
        startup_layout.addRow("", self.start_minimized_checkbox)
        
        self.move_to_desktop2_checkbox = QCheckBox("Move to Virtual Desktop 2 on startup")
        startup_layout.addRow("", self.move_to_desktop2_checkbox)
        
        self.auto_login_checkbox = QCheckBox("Attempt auto-login on startup")
        startup_layout.addRow("", self.auto_login_checkbox)
        
        layout.addWidget(startup_group)
        
        # UI Settings
        ui_group = QGroupBox("User Interface")
        ui_layout = QFormLayout()
        ui_group.setLayout(ui_layout)
        
        self.minimize_to_tray_checkbox = QCheckBox("Minimize to system tray instead of taskbar")
        ui_layout.addRow("", self.minimize_to_tray_checkbox)
        
        self.close_to_tray_checkbox = QCheckBox("Close to tray (don't exit)")
        ui_layout.addRow("", self.close_to_tray_checkbox)
        
        self.show_notifications_checkbox = QCheckBox("Show system notifications")
        ui_layout.addRow("", self.show_notifications_checkbox)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        ui_layout.addRow("Theme:", self.theme_combo)
        
        layout.addWidget(ui_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "General")
    
    def create_timing_tab(self):
        """Timing and delay settings"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Group Posting Delays
        group_delays_group = QGroupBox("Delays Between Groups")
        group_delays_layout = QFormLayout()
        group_delays_group.setLayout(group_delays_layout)
        
        # Min delay between groups
        self.min_group_delay_spin = QSpinBox()
        self.min_group_delay_spin.setRange(10, 600)  # 10 seconds to 10 minutes
        self.min_group_delay_spin.setSuffix(" seconds")
        self.min_group_delay_spin.setValue(60)
        group_delays_layout.addRow("Minimum delay:", self.min_group_delay_spin)
        
        # Max delay between groups
        self.max_group_delay_spin = QSpinBox()
        self.max_group_delay_spin.setRange(10, 600)
        self.max_group_delay_spin.setSuffix(" seconds")
        self.max_group_delay_spin.setValue(120)
        group_delays_layout.addRow("Maximum delay:", self.max_group_delay_spin)
        
        layout.addWidget(group_delays_group)
        
        # Page Loading Delays
        loading_group = QGroupBox("Page Loading & UI Delays")
        loading_layout = QFormLayout()
        loading_group.setLayout(loading_layout)
        
        # After navigation delay
        self.navigation_delay_spin = QSpinBox()
        self.navigation_delay_spin.setRange(1, 20)
        self.navigation_delay_spin.setSuffix(" seconds")
        self.navigation_delay_spin.setValue(5)
        loading_layout.addRow("After navigation:", self.navigation_delay_spin)
        
        # After button clicks
        self.click_delay_spin = QSpinBox()
        self.click_delay_spin.setRange(1, 10)
        self.click_delay_spin.setSuffix(" seconds")
        self.click_delay_spin.setValue(2)
        loading_layout.addRow("After button clicks:", self.click_delay_spin)
        
        # Image upload processing
        self.image_upload_delay_spin = QSpinBox()
        self.image_upload_delay_spin.setRange(2, 30)
        self.image_upload_delay_spin.setSuffix(" seconds")
        self.image_upload_delay_spin.setValue(5)
        loading_layout.addRow("Image upload processing:", self.image_upload_delay_spin)
        
        layout.addWidget(loading_group)
        
        # Retry Settings
        retry_group = QGroupBox("Retry & Error Handling")
        retry_layout = QFormLayout()
        retry_group.setLayout(retry_layout)
        
        # Failed post retry delay
        self.retry_delay_spin = QSpinBox()
        self.retry_delay_spin.setRange(5, 180)  # 5 minutes to 3 hours
        self.retry_delay_spin.setSuffix(" minutes")
        self.retry_delay_spin.setValue(30)
        retry_layout.addRow("Retry failed posts after:", self.retry_delay_spin)
        
        # Max retry attempts
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(0, 10)
        self.max_retries_spin.setValue(3)
        retry_layout.addRow("Maximum retry attempts:", self.max_retries_spin)
        
        layout.addWidget(retry_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Timing")
    
    def create_typing_tab(self):
        """Typing speed and behavior settings"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Typing Speed
        speed_group = QGroupBox("Typing Speed Settings")
        speed_layout = QFormLayout()
        speed_group.setLayout(speed_layout)
        
        # Typing speed preset
        self.typing_speed_combo = QComboBox()
        self.typing_speed_combo.addItems(["Instant", "Very Fast", "Fast", "Normal", "Slow", "Very Slow"])
        self.typing_speed_combo.setCurrentText("Fast")
        speed_layout.addRow("Typing speed preset:", self.typing_speed_combo)
        
        # Custom typing settings
        custom_group = QGroupBox("Custom Typing Settings")
        custom_layout = QFormLayout()
        custom_group.setLayout(custom_layout)
        
        # Character delay range
        self.min_char_delay_spin = QSpinBox()
        self.min_char_delay_spin.setRange(1, 500)
        self.min_char_delay_spin.setSuffix(" ms")
        self.min_char_delay_spin.setValue(20)
        custom_layout.addRow("Min delay per character:", self.min_char_delay_spin)
        
        self.max_char_delay_spin = QSpinBox()
        self.max_char_delay_spin.setRange(1, 500)
        self.max_char_delay_spin.setSuffix(" ms")
        self.max_char_delay_spin.setValue(80)
        custom_layout.addRow("Max delay per character:", self.max_char_delay_spin)
        
        # Pause settings
        self.pause_chance_spin = QSpinBox()
        self.pause_chance_spin.setRange(0, 50)
        self.pause_chance_spin.setSuffix(" %")
        self.pause_chance_spin.setValue(5)
        custom_layout.addRow("Random pause chance:", self.pause_chance_spin)
        
        layout.addWidget(speed_group)
        layout.addWidget(custom_group)
        
        # Typing Behavior
        behavior_group = QGroupBox("Typing Behavior")
        behavior_layout = QFormLayout()
        behavior_group.setLayout(behavior_layout)
        
        self.enable_human_typing_checkbox = QCheckBox("Enable human-like typing patterns")
        behavior_layout.addRow("", self.enable_human_typing_checkbox)
        
        self.random_pauses_checkbox = QCheckBox("Random pauses during long text")
        behavior_layout.addRow("", self.random_pauses_checkbox)
        
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Typing")
    
    def create_posting_tab(self):
        """Posting behavior settings"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Posting Behavior
        posting_group = QGroupBox("Posting Behavior")
        posting_layout = QFormLayout()
        posting_group.setLayout(posting_layout)
        
        # Default frequency
        self.default_frequency_spin = QSpinBox()
        self.default_frequency_spin.setRange(1, 168)  # 1 hour to 1 week
        self.default_frequency_spin.setSuffix(" hours")
        self.default_frequency_spin.setValue(24)
        posting_layout.addRow("Default posting frequency:", self.default_frequency_spin)
        
        # Start immediately by default
        self.default_start_immediately_checkbox = QCheckBox("Start new automations immediately by default")
        posting_layout.addRow("", self.default_start_immediately_checkbox)
        
        # Verify groups automatically
        self.auto_verify_groups_checkbox = QCheckBox("Auto-verify group membership when adding")
        posting_layout.addRow("", self.auto_verify_groups_checkbox)
        
        layout.addWidget(posting_group)
        
        # Image Settings
        image_group = QGroupBox("Image Upload Settings")
        image_layout = QFormLayout()
        image_group.setLayout(image_layout)
        
        # Upload method
        self.upload_method_combo = QComboBox()
        self.upload_method_combo.addItems(["HTML5 Drag & Drop", "Direct File Input", "PyAutoGUI Fallback"])
        image_layout.addRow("Preferred upload method:", self.upload_method_combo)
        
        # Max image size
        self.max_image_size_spin = QSpinBox()
        self.max_image_size_spin.setRange(1, 50)
        self.max_image_size_spin.setSuffix(" MB")
        self.max_image_size_spin.setValue(10)
        image_layout.addRow("Maximum image size:", self.max_image_size_spin)
        
        # Image quality/compression
        self.compress_images_checkbox = QCheckBox("Compress large images automatically")
        image_layout.addRow("", self.compress_images_checkbox)
        
        layout.addWidget(image_group)
        
        # Queue Settings
        queue_group = QGroupBox("Queue & Execution")
        queue_layout = QFormLayout()
        queue_group.setLayout(queue_layout)
        
        # Check interval
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(5, 120)  # 5 seconds to 2 minutes
        self.check_interval_spin.setSuffix(" seconds")
        self.check_interval_spin.setValue(15)
        queue_layout.addRow("Check for due posts every:", self.check_interval_spin)
        
        # Max concurrent automations
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 10)
        self.max_concurrent_spin.setValue(1)
        queue_layout.addRow("Max concurrent executions:", self.max_concurrent_spin)
        
        layout.addWidget(queue_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Posting")
    
    def create_advanced_tab(self):
        """Advanced settings"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Browser Settings
        browser_group = QGroupBox("Browser Settings")
        browser_layout = QFormLayout()
        browser_group.setLayout(browser_layout)
        
        # Headless mode
        self.headless_mode_checkbox = QCheckBox("Run browser in headless mode (invisible)")
        browser_layout.addRow("", self.headless_mode_checkbox)
        
        # User agent
        self.custom_user_agent_checkbox = QCheckBox("Use custom user agent")
        browser_layout.addRow("", self.custom_user_agent_checkbox)
        
        self.user_agent_edit = QLineEdit()
        self.user_agent_edit.setPlaceholderText("Leave empty for default")
        browser_layout.addRow("User agent:", self.user_agent_edit)
        
        # Window size
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 3840)
        self.window_width_spin.setValue(1366)
        browser_layout.addRow("Browser width:", self.window_width_spin)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 2160)
        self.window_height_spin.setValue(768)
        browser_layout.addRow("Browser height:", self.window_height_spin)
        
        layout.addWidget(browser_group)
        
        # Logging Settings
        logging_group = QGroupBox("Logging & Debug")
        logging_layout = QFormLayout()
        logging_group.setLayout(logging_layout)
        
        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        logging_layout.addRow("Log level:", self.log_level_combo)
        
        # Keep logs for X days
        self.log_retention_spin = QSpinBox()
        self.log_retention_spin.setRange(1, 365)
        self.log_retention_spin.setSuffix(" days")
        self.log_retention_spin.setValue(30)
        logging_layout.addRow("Keep logs for:", self.log_retention_spin)
        
        # Detailed logging
        self.detailed_logging_checkbox = QCheckBox("Enable detailed execution logging")
        logging_layout.addRow("", self.detailed_logging_checkbox)
        
        layout.addWidget(logging_group)
        
        # Data Settings
        data_group = QGroupBox("Data Management")
        data_layout = QFormLayout()
        data_group.setLayout(data_layout)
        
        # Auto-backup
        self.auto_backup_checkbox = QCheckBox("Auto-backup data weekly")
        data_layout.addRow("", self.auto_backup_checkbox)
        
        # Cleanup old data
        self.cleanup_old_data_checkbox = QCheckBox("Auto-cleanup old verification data")
        data_layout.addRow("", self.cleanup_old_data_checkbox)
        
        # Data location button
        data_location_button = QPushButton("📁 Open Data Folder")
        data_location_button.clicked.connect(self.open_data_folder)
        data_layout.addRow("", data_location_button)
        
        layout.addWidget(data_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Advanced")
    
    def get_default_settings(self):
        """Get default settings dictionary"""
        return {
            # General
            'auto_start': False,
            'start_minimized': False,
            'move_to_desktop2': False,
            'auto_login': True,
            'minimize_to_tray': True,
            'close_to_tray': True,
            'show_notifications': True,
            'theme': 'Light',
            
            # Timing
            'min_group_delay': 60,
            'max_group_delay': 120,
            'navigation_delay': 5,
            'click_delay': 2,
            'image_upload_delay': 5,
            'retry_delay_minutes': 30,
            'max_retries': 3,
            
            # Typing
            'typing_speed_preset': 'Fast',
            'min_char_delay_ms': 20,
            'max_char_delay_ms': 80,
            'pause_chance_percent': 5,
            'enable_human_typing': True,
            'random_pauses': True,
            
            # Posting
            'default_frequency_hours': 24,
            'default_start_immediately': True,
            'auto_verify_groups': True,
            'upload_method': 'HTML5 Drag & Drop',
            'max_image_size_mb': 10,
            'compress_images': False,
            'check_interval_seconds': 15,
            'max_concurrent': 1,
            
            # Advanced
            'headless_mode': False,
            'custom_user_agent_enabled': False,
            'user_agent': '',
            'window_width': 1366,
            'window_height': 768,
            'log_level': 'INFO',
            'log_retention_days': 30,
            'detailed_logging': False,
            'auto_backup': True,
            'cleanup_old_data': True
        }
    
    def load_settings(self):
        """Load settings from file"""
        try:
            settings_file = os.path.join('data', 'settings.json')
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                default_settings = self.get_default_settings()
                default_settings.update(loaded_settings)
                return default_settings
            else:
                return self.get_default_settings()
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            return self.get_default_settings()
    
    def save_settings_to_file(self):
        """Save settings to file"""
        try:
            os.makedirs('data', exist_ok=True)
            settings_file = os.path.join('data', 'settings.json')
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Settings saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            return False
    
    def load_current_settings(self):
        """Load current settings into UI controls"""
        # General tab
        self.auto_start_checkbox.setChecked(self.settings.get('auto_start', False))
        self.start_minimized_checkbox.setChecked(self.settings.get('start_minimized', False))
        self.move_to_desktop2_checkbox.setChecked(self.settings.get('move_to_desktop2', False))
        self.auto_login_checkbox.setChecked(self.settings.get('auto_login', True))
        self.minimize_to_tray_checkbox.setChecked(self.settings.get('minimize_to_tray', True))
        self.close_to_tray_checkbox.setChecked(self.settings.get('close_to_tray', True))
        self.show_notifications_checkbox.setChecked(self.settings.get('show_notifications', True))
        self.theme_combo.setCurrentText(self.settings.get('theme', 'Light'))
        
        # Timing tab
        self.min_group_delay_spin.setValue(self.settings.get('min_group_delay', 60))
        self.max_group_delay_spin.setValue(self.settings.get('max_group_delay', 120))
        self.navigation_delay_spin.setValue(self.settings.get('navigation_delay', 5))
        self.click_delay_spin.setValue(self.settings.get('click_delay', 2))
        self.image_upload_delay_spin.setValue(self.settings.get('image_upload_delay', 5))
        self.retry_delay_spin.setValue(self.settings.get('retry_delay_minutes', 30))
        self.max_retries_spin.setValue(self.settings.get('max_retries', 3))
        
        # Typing tab
        self.typing_speed_combo.setCurrentText(self.settings.get('typing_speed_preset', 'Fast'))
        self.min_char_delay_spin.setValue(self.settings.get('min_char_delay_ms', 20))
        self.max_char_delay_spin.setValue(self.settings.get('max_char_delay_ms', 80))
        self.pause_chance_spin.setValue(self.settings.get('pause_chance_percent', 5))
        self.enable_human_typing_checkbox.setChecked(self.settings.get('enable_human_typing', True))
        self.random_pauses_checkbox.setChecked(self.settings.get('random_pauses', True))
        
        # Posting tab
        self.default_frequency_spin.setValue(self.settings.get('default_frequency_hours', 24))
        self.default_start_immediately_checkbox.setChecked(self.settings.get('default_start_immediately', True))
        self.auto_verify_groups_checkbox.setChecked(self.settings.get('auto_verify_groups', True))
        self.upload_method_combo.setCurrentText(self.settings.get('upload_method', 'HTML5 Drag & Drop'))
        self.max_image_size_spin.setValue(self.settings.get('max_image_size_mb', 10))
        self.compress_images_checkbox.setChecked(self.settings.get('compress_images', False))
        self.check_interval_spin.setValue(self.settings.get('check_interval_seconds', 15))
        self.max_concurrent_spin.setValue(self.settings.get('max_concurrent', 1))
        
        # Advanced tab
        self.headless_mode_checkbox.setChecked(self.settings.get('headless_mode', False))
        self.custom_user_agent_checkbox.setChecked(self.settings.get('custom_user_agent_enabled', False))
        self.user_agent_edit.setText(self.settings.get('user_agent', ''))
        self.window_width_spin.setValue(self.settings.get('window_width', 1366))
        self.window_height_spin.setValue(self.settings.get('window_height', 768))
        self.log_level_combo.setCurrentText(self.settings.get('log_level', 'INFO'))
        self.log_retention_spin.setValue(self.settings.get('log_retention_days', 30))
        self.detailed_logging_checkbox.setChecked(self.settings.get('detailed_logging', False))
        self.auto_backup_checkbox.setChecked(self.settings.get('auto_backup', True))
        self.cleanup_old_data_checkbox.setChecked(self.settings.get('cleanup_old_data', True))
    
    def save_settings(self):
        """Save all settings from UI to settings dict"""
        try:
            # General
            self.settings['auto_start'] = self.auto_start_checkbox.isChecked()
            self.settings['start_minimized'] = self.start_minimized_checkbox.isChecked()
            self.settings['move_to_desktop2'] = self.move_to_desktop2_checkbox.isChecked()
            self.settings['auto_login'] = self.auto_login_checkbox.isChecked()
            self.settings['minimize_to_tray'] = self.minimize_to_tray_checkbox.isChecked()
            self.settings['close_to_tray'] = self.close_to_tray_checkbox.isChecked()
            self.settings['show_notifications'] = self.show_notifications_checkbox.isChecked()
            self.settings['theme'] = self.theme_combo.currentText()
            
            # Timing
            self.settings['min_group_delay'] = self.min_group_delay_spin.value()
            self.settings['max_group_delay'] = self.max_group_delay_spin.value()
            self.settings['navigation_delay'] = self.navigation_delay_spin.value()
            self.settings['click_delay'] = self.click_delay_spin.value()
            self.settings['image_upload_delay'] = self.image_upload_delay_spin.value()
            self.settings['retry_delay_minutes'] = self.retry_delay_spin.value()
            self.settings['max_retries'] = self.max_retries_spin.value()
            
            # Typing
            self.settings['typing_speed_preset'] = self.typing_speed_combo.currentText()
            self.settings['min_char_delay_ms'] = self.min_char_delay_spin.value()
            self.settings['max_char_delay_ms'] = self.max_char_delay_spin.value()
            self.settings['pause_chance_percent'] = self.pause_chance_spin.value()
            self.settings['enable_human_typing'] = self.enable_human_typing_checkbox.isChecked()
            self.settings['random_pauses'] = self.random_pauses_checkbox.isChecked()
            
            # Posting
            self.settings['default_frequency_hours'] = self.default_frequency_spin.value()
            self.settings['default_start_immediately'] = self.default_start_immediately_checkbox.isChecked()
            self.settings['auto_verify_groups'] = self.auto_verify_groups_checkbox.isChecked()
            self.settings['upload_method'] = self.upload_method_combo.currentText()
            self.settings['max_image_size_mb'] = self.max_image_size_spin.value()
            self.settings['compress_images'] = self.compress_images_checkbox.isChecked()
            self.settings['check_interval_seconds'] = self.check_interval_spin.value()
            self.settings['max_concurrent'] = self.max_concurrent_spin.value()
            
            # Advanced
            self.settings['headless_mode'] = self.headless_mode_checkbox.isChecked()
            self.settings['custom_user_agent_enabled'] = self.custom_user_agent_checkbox.isChecked()
            self.settings['user_agent'] = self.user_agent_edit.text()
            self.settings['window_width'] = self.window_width_spin.value()
            self.settings['window_height'] = self.window_height_spin.value()
            self.settings['log_level'] = self.log_level_combo.currentText()
            self.settings['log_retention_days'] = self.log_retention_spin.value()
            self.settings['detailed_logging'] = self.detailed_logging_checkbox.isChecked()
            self.settings['auto_backup'] = self.auto_backup_checkbox.isChecked()
            self.settings['cleanup_old_data'] = self.cleanup_old_data_checkbox.isChecked()
            
            # Validate settings
            if self.settings['min_group_delay'] > self.settings['max_group_delay']:
                QMessageBox.warning(self, "Invalid Settings", 
                                  "Minimum group delay cannot be greater than maximum delay.")
                return
            
            if self.settings['min_char_delay_ms'] > self.settings['max_char_delay_ms']:
                QMessageBox.warning(self, "Invalid Settings", 
                                  "Minimum character delay cannot be greater than maximum delay.")
                return
            
            # Save to file
            if self.save_settings_to_file():
                self.settings_changed.emit()
                QMessageBox.information(self, "Settings Saved", 
                                      "Settings have been saved successfully!")
                self.accept()
            else:
                QMessageBox.critical(self, "Save Error", 
                                   "Failed to save settings to file.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while saving: {str(e)}")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(self, "Reset Settings",
                                   "Are you sure you want to reset all settings to defaults?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.settings = self.get_default_settings()
            self.load_current_settings()
    
    def open_data_folder(self):
        """Open the data folder in file explorer"""
        try:
            import subprocess
            import platform
            
            data_path = os.path.abspath('data')
            
            if platform.system() == 'Windows':
                subprocess.run(['explorer', data_path])
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', data_path])
            else:  # Linux
                subprocess.run(['xdg-open', data_path])
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open data folder: {str(e)}")

# Helper function to get current settings
def get_current_settings():
    """Get current settings from file"""
    try:
        settings_file = os.path.join('data', 'settings.json')
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    
    # Return defaults if file doesn't exist or can't be read
    return SettingsDialog(None).get_default_settings()
