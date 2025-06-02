"""
Main Window - Primary GUI Interface
Central hub for managing all automation activities
"""

import sys
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QGroupBox, QStatusBar, QMenuBar, QAction,
                             QMessageBox, QDialog, QSplitter, QFrame)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor

from ui.template_editor import TemplateEditorDialog
from ui.automation_manager import AutomationManagerDialog
from ui.login_dialog import LoginDialog
from core.facebook_login import FacebookLogin
from core.group_poster import GroupPoster
from templates.template_manager import TemplateManager


class MainWindow(QMainWindow):
    def __init__(self, scheduler, file_manager):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.scheduler = scheduler
        self.file_manager = file_manager
        self.template_manager = TemplateManager()
        
        
        # Initialize core components
        self.facebook_login = FacebookLogin()
        self.group_poster = GroupPoster(self.facebook_login)
        
        # Set dependencies
        self.scheduler.set_dependencies(self.facebook_login, self.group_poster)
        
        self.init_ui()
        self.setup_timers()
        self.update_displays()

        
        
        # Auto-login on startup if credentials exist
        self.auto_login()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Facebook Groups Post Automation Tool")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
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
            QPushButton:pressed {
                background-color: #29487d;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status section
        self.create_status_section(main_layout)
        
        # Create main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Quick Actions
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Active Automations
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        # Create status bar
        self.create_status_bar()

        # Add settings button to toolbar or menu
        settings_button = QPushButton("⚙️ Settings")
        settings_button.clicked.connect(self.show_settings)
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        login_action = QAction('Login to Facebook', self)
        login_action.triggered.connect(self.show_login_dialog)
        file_menu.addAction(login_action)
        
        logout_action = QAction('Logout', self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Templates menu
        templates_menu = menubar.addMenu('Templates')
        
        new_template_action = QAction('New Template', self)
        new_template_action.triggered.connect(self.show_template_editor)
        templates_menu.addAction(new_template_action)
        
        manage_templates_action = QAction('Manage Templates', self)
        manage_templates_action.triggered.connect(self.show_template_manager)
        templates_menu.addAction(manage_templates_action)
        
        # Automation menu
        automation_menu = menubar.addMenu('Automation')
        
        new_automation_action = QAction('New Automation', self)
        new_automation_action.triggered.connect(self.show_automation_manager)
        automation_menu.addAction(new_automation_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_status_section(self, layout):
        """Create login status and quick info section"""
        status_group = QGroupBox("System Status")
        status_layout = QHBoxLayout()
        status_group.setLayout(status_layout)
        
        # Login status
        self.login_status_label = QLabel("Not logged in")
        self.login_status_label.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(QLabel("Facebook Status:"))
        status_layout.addWidget(self.login_status_label)
        
        status_layout.addWidget(self.create_separator())
        
        # Active automations count
        self.active_count_label = QLabel("0")
        self.active_count_label.setStyleSheet("color: green; font-weight: bold;")
        status_layout.addWidget(QLabel("Active Automations:"))
        status_layout.addWidget(self.active_count_label)
        
        status_layout.addWidget(self.create_separator())
        
        # Templates count
        self.templates_count_label = QLabel("0")
        status_layout.addWidget(QLabel("Templates:"))
        status_layout.addWidget(self.templates_count_label)
        
        status_layout.addStretch()
        
        layout.addWidget(status_group)
    
    def create_left_panel(self):
        """Create left panel with quick actions"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # Quick Actions Group
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout()
        actions_group.setLayout(actions_layout)
        
        # Login button
        self.login_btn = QPushButton("🔐 Login to Facebook")
        self.login_btn.clicked.connect(self.show_login_dialog)
        actions_layout.addWidget(self.login_btn)
        
        # Create template button
        create_template_btn = QPushButton("📝 Create New Template")
        create_template_btn.clicked.connect(self.show_template_editor)
        actions_layout.addWidget(create_template_btn)
        
        # Create automation button
        self.create_automation_btn = QPushButton("⚙️ New Automation")
        self.create_automation_btn.clicked.connect(self.show_automation_manager)
        self.create_automation_btn.setEnabled(False)
        actions_layout.addWidget(self.create_automation_btn)
        
        # ADD SETTINGS BUTTON HERE
        settings_btn = QPushButton("🛠️ Settings")
        settings_btn.clicked.connect(self.show_settings)
        settings_btn.setToolTip("Configure automation settings and preferences")
        actions_layout.addWidget(settings_btn)
        
        actions_layout.addStretch()
        
        left_layout.addWidget(actions_group)
        
        # Templates Preview Group
        templates_group = QGroupBox("Templates")
        templates_layout = QVBoxLayout()
        templates_group.setLayout(templates_layout)
        
        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(2)
        self.templates_table.setHorizontalHeaderLabels(["Name", "Created"])
        self.templates_table.horizontalHeader().setStretchLastSection(True)
        self.templates_table.setMaximumHeight(200)
        templates_layout.addWidget(self.templates_table)
        
        manage_templates_btn = QPushButton("Manage Templates")
        manage_templates_btn.clicked.connect(self.show_template_manager)
        templates_layout.addWidget(manage_templates_btn)
        
        left_layout.addWidget(templates_group)
        left_layout.addStretch()
        
        return left_widget
    
    def create_right_panel(self):
        """Create right panel with active automations"""
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        # Active Automations Group
        automations_group = QGroupBox("Active Automations")
        automations_layout = QVBoxLayout()
        automations_group.setLayout(automations_layout)
        
        # Automations table
        self.automations_table = QTableWidget()
        self.automations_table.setColumnCount(6)
        self.automations_table.setHorizontalHeaderLabels([
            "Template", "Groups", "Status", "Next Post", "Frequency", "Actions"
        ])
        
        # Configure table
        header = self.automations_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        automations_layout.addWidget(self.automations_table)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.update_displays)
        control_layout.addWidget(refresh_btn)
        
        control_layout.addStretch()
        
        pause_all_btn = QPushButton("⏸️ Pause All")
        pause_all_btn.clicked.connect(self.pause_all_automations)
        control_layout.addWidget(pause_all_btn)
        
        resume_all_btn = QPushButton("▶️ Resume All")
        resume_all_btn.clicked.connect(self.resume_all_automations)
        control_layout.addWidget(resume_all_btn)
        
        automations_layout.addLayout(control_layout)
        
        right_layout.addWidget(automations_group)
        
        return right_widget
    
    def create_separator(self):
        """Create a vertical separator line"""
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        return separator
    
    def create_status_bar(self):
        """Create application status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def setup_timers(self):
        """Setup timers for periodic updates"""
        # Update display every 30 seconds
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_displays)
        self.update_timer.start(30000)
        
        # Check login status every 5 minutes
        self.login_check_timer = QTimer()
        self.login_check_timer.timeout.connect(self.check_login_status)
        self.login_check_timer.start(300000)
        
        # ✅ ADD THIS MISSING SCHEDULER TIMER:
        self.scheduler_timer = QTimer()
        self.scheduler_timer.timeout.connect(self.scheduler.check_scheduled_posts)
        self.scheduler_timer.start(15000)  # 15 seconds
        self.logger.info("All timers setup completed")
    
    def auto_login(self):
        """Enhanced automatic login with better detection"""
        try:
            self.status_bar.showMessage("Checking login status...")
            
            # Initialize driver first
            self.facebook_login.driver = self.facebook_login.web_manager.get_driver(use_existing_profile=True)
            
            # Check if already logged in via profile
            self.facebook_login.driver.get("https://www.facebook.com")
            self.facebook_login.web_manager.random_delay(3, 5)
            
            if self.facebook_login.is_session_valid():
                self.facebook_login.is_logged_in = True
                self.facebook_login.save_session()
                self.update_login_status(True)
                self.status_bar.showMessage("Already logged in via profile")
                self.logger.info("Auto-login successful - already logged in")
                return
            
            # Try regular login process
            if self.facebook_login.login():
                self.update_login_status(True)
                self.status_bar.showMessage("Auto-login successful")
            else:
                self.status_bar.showMessage("Auto-login failed - manual login required")
                
        except Exception as e:
            self.logger.error(f"Auto-login error: {e}")
            self.status_bar.showMessage(f"Auto-login error: {str(e)}")

    
    def show_login_dialog(self):
        """Show Facebook login dialog"""
        dialog = LoginDialog(self.facebook_login, self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_login_status(True)
            self.status_bar.showMessage("Login successful")
        else:
            self.status_bar.showMessage("Login cancelled or failed")
    
    def show_template_editor(self, template_id=None):
        """Show template editor dialog"""
        dialog = TemplateEditorDialog(self.template_manager, template_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_displays()
            self.status_bar.showMessage("Template saved successfully")
    
    def show_template_manager(self):
        """Show template management dialog"""
        from ui.template_manager_dialog import TemplateManagerDialog
        dialog = TemplateManagerDialog(self.template_manager, self)
        dialog.exec_()
        self.update_displays()
    
    def show_automation_manager(self):
        """Show automation creation dialog"""
        if not self.facebook_login.is_logged_in:
            QMessageBox.warning(self, "Login Required", 
                              "Please log into Facebook before creating automations.")
            return
        
        dialog = AutomationManagerDialog(self.scheduler, self.template_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_displays()
            self.status_bar.showMessage("Automation created successfully")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", 
                         "Facebook Groups Post Automation Tool\n\n"
                         "Automates posting to Facebook groups with templates\n"
                         "and flexible scheduling.\n\n"
                         "⚠️ Creates NEW posts only - never comments on existing posts")
    
    def update_login_status(self, is_logged_in):
        """Update login status display"""
        if is_logged_in:
            self.login_status_label.setText("✅ Logged In")
            self.login_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.login_btn.setText("🔐 Logged In")
            self.login_btn.setEnabled(False)
            self.create_automation_btn.setEnabled(True)
        else:
            self.login_status_label.setText("❌ Not Logged In")
            self.login_status_label.setStyleSheet("color: red; font-weight: bold;")
            self.login_btn.setText("🔐 Login to Facebook")
            self.login_btn.setEnabled(True)
            self.create_automation_btn.setEnabled(False)
    
    def check_login_status(self):
        """Periodically check if still logged in"""
        if self.facebook_login.is_logged_in:
            # Verify session is still valid
            if not self.facebook_login.is_session_valid():
                self.update_login_status(False)
                self.status_bar.showMessage("Session expired - please log in again")
    
    def update_displays(self):
        """Update all display elements"""
        self.update_templates_display()
        self.update_automations_display()
        self.update_counters()
    
    def update_templates_display(self):
        """Update templates table"""
        templates = self.template_manager.get_all_templates()
        self.templates_table.setRowCount(len(templates))
        
        for row, (template_id, template) in enumerate(templates.items()):
            # Template name
            name_item = QTableWidgetItem(template.name)
            self.templates_table.setItem(row, 0, name_item)
            
            # Created date
            created_date = datetime.fromtimestamp(template.created_at).strftime("%m/%d %H:%M")
            date_item = QTableWidgetItem(created_date)
            self.templates_table.setItem(row, 1, date_item)
    
    def update_automations_display(self):
        """Update automations table"""
        scheduled_posts = self.scheduler.get_scheduled_posts()
        self.automations_table.setRowCount(len(scheduled_posts))
        
        template_names = self.template_manager.get_template_names()
        
        for row, (post_id, scheduled_post) in enumerate(scheduled_posts.items()):
            # Template name
            template_name = template_names.get(scheduled_post.template_id, "Unknown")
            template_item = QTableWidgetItem(template_name)
            self.automations_table.setItem(row, 0, template_item)
            
            # Groups count
            groups_item = QTableWidgetItem(f"{len(scheduled_post.group_urls)} groups")
            self.automations_table.setItem(row, 1, groups_item)
            
            # Status
            status_item = QTableWidgetItem(scheduled_post.status.value.title())
            if scheduled_post.status.value == "ongoing":
                status_item.setBackground(QColor("#d4edda"))
            elif scheduled_post.status.value == "paused":
                status_item.setBackground(QColor("#fff3cd"))
            else:
                status_item.setBackground(QColor("#f8d7da"))
            self.automations_table.setItem(row, 2, status_item)
            
            # Next post time
            if scheduled_post.next_post_time:
                next_time = datetime.fromtimestamp(scheduled_post.next_post_time)
                time_str = next_time.strftime("%m/%d %H:%M")
            else:
                time_str = "Not scheduled"
            time_item = QTableWidgetItem(time_str)
            self.automations_table.setItem(row, 3, time_item)
            
            # Frequency
            freq_item = QTableWidgetItem(f"Every {scheduled_post.frequency_hours}h")
            self.automations_table.setItem(row, 4, freq_item)
            
            # Action buttons
            actions_widget = self.create_action_buttons(post_id, scheduled_post)
            self.automations_table.setCellWidget(row, 5, actions_widget)
    
    def create_action_buttons(self, post_id, scheduled_post):
        """Create action buttons for automation row"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        widget.setLayout(layout)
        
        # Test/Force Execute button (for debugging)
        test_btn = QPushButton("🚀")
        test_btn.setToolTip("Test post now (force execute)")
        test_btn.setMaximumWidth(30)
        test_btn.clicked.connect(lambda: self.force_execute_post(post_id))
        layout.addWidget(test_btn)
        
        if scheduled_post.status.value == "ongoing":
            pause_btn = QPushButton("⏸️")
            pause_btn.setToolTip("Pause automation")
            pause_btn.setMaximumWidth(30)
            pause_btn.clicked.connect(lambda: self.pause_automation(post_id))
            layout.addWidget(pause_btn)
        elif scheduled_post.status.value == "paused":
            resume_btn = QPushButton("▶️")
            resume_btn.setToolTip("Resume automation")
            resume_btn.setMaximumWidth(30)
            resume_btn.clicked.connect(lambda: self.resume_automation(post_id))
            layout.addWidget(resume_btn)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("Edit automation")
        edit_btn.setMaximumWidth(30)
        edit_btn.clicked.connect(lambda: self.edit_automation(post_id))
        layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setToolTip("Delete automation")
        delete_btn.setMaximumWidth(30)
        delete_btn.clicked.connect(lambda: self.delete_automation(post_id))
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        return widget
    
    def force_execute_post(self, post_id):
        """Force execute a post for testing"""
        if self.scheduler.force_execute_post(post_id):
            self.status_bar.showMessage("Force executing post...")
            QMessageBox.information(self, "Test Execution", 
                                "Post execution started. Check logs for progress.")
        else:
            QMessageBox.warning(self, "Execution Failed", 
                            "Could not execute post. Check if automation is active.")
        
    def update_counters(self):
        """Update status counters with safe queue information"""
        try:
            templates = self.template_manager.get_all_templates()
            self.templates_count_label.setText(str(len(templates)))
            
            scheduled_posts = self.scheduler.get_scheduled_posts()
            active_count = sum(1 for post in scheduled_posts.values() 
                            if post.status.value == "ongoing")
            
            # ✅ SAFE queue status check
            try:
                queue_status = self.scheduler.get_queue_status()
                queue_size = queue_status.get('queue_size', 0)
                is_processing = queue_status.get('is_processing', False)
                
                status_text = f"{active_count}"
                if queue_size > 0:
                    status_text += f" (Queue: {queue_size})"
                if is_processing:
                    status_text += " 🔄"
            except (AttributeError, KeyError, TypeError):
                # Fallback if queue status not available
                status_text = str(active_count)
            
            self.active_count_label.setText(status_text)
            
        except Exception as e:
            self.logger.error(f"Counter update failed: {e}")

    
    def pause_automation(self, post_id):
        """Pause a specific automation"""
        if self.scheduler.pause_automation(post_id):
            self.update_displays()
            self.status_bar.showMessage("Automation paused")
    
    def resume_automation(self, post_id):
        """Resume a specific automation"""
        if self.scheduler.resume_automation(post_id):
            self.update_displays()
            self.status_bar.showMessage("Automation resumed")
    
    def edit_automation(self, post_id):
        """Edit a specific automation"""
        # TODO: Implement edit automation dialog
        QMessageBox.information(self, "Edit Automation", 
                               "Edit automation feature coming soon!")
    
    def delete_automation(self, post_id):
        """Delete a specific automation"""
        reply = QMessageBox.question(self, "Delete Automation",
                                   "Are you sure you want to delete this automation?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.scheduler.delete_automation(post_id):
                self.update_displays()
                self.status_bar.showMessage("Automation deleted")
    
    def pause_all_automations(self):
        """Pause all active automations"""
        scheduled_posts = self.scheduler.get_scheduled_posts()
        paused_count = 0
        
        for post_id, scheduled_post in scheduled_posts.items():
            if scheduled_post.status.value == "ongoing":
                if self.scheduler.pause_automation(post_id):
                    paused_count += 1
        
        self.update_displays()
        self.status_bar.showMessage(f"Paused {paused_count} automations")
    
    def resume_all_automations(self):
        """Resume all paused automations"""
        scheduled_posts = self.scheduler.get_scheduled_posts()
        resumed_count = 0
        
        for post_id, scheduled_post in scheduled_posts.items():
            if scheduled_post.status.value == "paused":
                if self.scheduler.resume_automation(post_id):
                    resumed_count += 1
        
        self.update_displays()
        self.status_bar.showMessage(f"Resumed {resumed_count} automations")
    
    def logout(self):
        """Logout from Facebook"""
        self.facebook_login.logout()
        self.update_login_status(False)
        self.status_bar.showMessage("Logged out successfully")
    
    def closeEvent(self, event):
        """Handle application close with proper cleanup"""
        reply = QMessageBox.question(self, "Exit Application",
                                "Are you sure you want to exit?\n"
                                "All running automations will be stopped.",
                                QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                self.logger.info("Application shutdown initiated...")
                
                # Stop all timers first
                if hasattr(self, 'update_timer') and self.update_timer:
                    self.update_timer.stop()
                    self.logger.info("Update timer stopped")
                
                if hasattr(self, 'login_check_timer') and self.login_check_timer:
                    self.login_check_timer.stop()
                    self.logger.info("Login check timer stopped")
                
                if hasattr(self, 'scheduler_timer') and self.scheduler_timer:
                    self.scheduler_timer.stop()
                    self.logger.info("Scheduler timer stopped")
                
                # Save current state
                if self.scheduler:
                    self.scheduler.save_scheduled_posts()
                    self.logger.info("Scheduled posts saved")
                
                if self.template_manager:
                    self.template_manager.save_templates()
                    self.logger.info("Templates saved")
                
                # Proper WebDriver cleanup
                if self.facebook_login:
                    if hasattr(self.facebook_login, 'driver') and self.facebook_login.driver:
                        try:
                            self.facebook_login.driver.quit()
                            self.logger.info("WebDriver closed properly")
                        except Exception as e:
                            self.logger.warning(f"WebDriver cleanup warning: {e}")
                    
                    # Logout
                    self.facebook_login.logout()
                    self.logger.info("Facebook logout completed")
                
                self.logger.info("Application shutdown completed successfully")
                
            except Exception as e:
                self.logger.error(f"Error during application shutdown: {e}")
            
            event.accept()
        else:
            event.ignore()


    def show_settings(self):
        """Show settings dialog"""
        from ui.settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.apply_settings)
        dialog.exec_()

    def apply_settings(self):
        """Apply changed settings"""
        try:
            from ui.settings_dialog import get_current_settings
            
            settings = get_current_settings()
            
            # Update scheduler check interval
            check_interval = settings.get('check_interval_seconds', 15) * 1000
            if hasattr(self, 'update_timer'):
                self.update_timer.setInterval(check_interval)
                self.logger.info(f"Updated check interval to {check_interval/1000} seconds")
            
            # Update theme if changed
            theme = settings.get('theme', 'Light')
            if theme == 'Dark':
                self.apply_dark_theme()
            else:
                self.apply_light_theme()
            
            # Show notification if enabled
            if settings.get('show_notifications', True):
                self.status_bar.showMessage("Settings applied successfully!", 3000)
            
            self.logger.info("Settings applied successfully")
            
        except ImportError:
            QMessageBox.critical(self, "Error", 
                            "Settings dialog not available. Make sure ui/settings_dialog.py exists.")
        except Exception as e:
            self.logger.error(f"Failed to apply settings: {e}")
            QMessageBox.warning(self, "Settings Error", 
                            f"Some settings could not be applied: {e}")

    def apply_dark_theme(self):
        """Apply dark theme"""
        dark_style = """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                background-color: #3c3c3c;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 1ex;
                color: #ffffff;
            }
            QPushButton {
                background-color: #4267B2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #365899;
            }
            QTableWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
            }
        """
        self.setStyleSheet(dark_style)

    def apply_light_theme(self):
        """Apply light theme (your current theme)"""
        # This resets to your current stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
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
            QPushButton:pressed {
                background-color: #29487d;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

