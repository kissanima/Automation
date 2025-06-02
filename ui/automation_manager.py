"""
Automation Manager - Create and Configure Post Automations
Set up automated posting schedules with templates and target groups
"""

import time
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QSpinBox, QListWidget, QListWidgetItem,
                             QPushButton, QTextEdit, QGroupBox, QFormLayout,
                             QCheckBox, QMessageBox, QLineEdit, QFrame,
                             QScrollArea, QWidget)  # Added QScrollArea and QWidget
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from utils.file_manager import FileManager  # Add this import



class GroupVerificationWorker(QThread):
    """Worker thread for verifying group membership"""
    verification_complete = pyqtSignal(str, bool)  # group_url, is_member
    
    def __init__(self, group_poster, group_urls):
        super().__init__()
        self.group_poster = group_poster
        self.group_urls = group_urls
    
    def run(self):
        """Verify membership for each group"""
        for group_url in self.group_urls:
            try:
                is_member = self.group_poster.verify_group_membership(group_url)
                self.verification_complete.emit(group_url, is_member)
            except Exception as e:
                self.verification_complete.emit(group_url, False)

class AutomationManagerDialog(QDialog):
    def __init__(self, scheduler, template_manager, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.scheduler = scheduler
        self.template_manager = template_manager
        self.file_manager = parent.file_manager if parent else FileManager()  # Get file_manager from parent
        self.group_urls = []
        self.verified_groups = {}
        self.verification_worker = None
        
        self.init_ui()
        self.load_templates()
        self.load_saved_verified_groups()
    
    def init_ui(self):
        """Initialize automation manager UI"""
        self.setWindowTitle("Create New Automation")
        self.setGeometry(250, 250, 700, 700)  # Increased height
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_label = QLabel("⚙️ Create New Post Automation")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(header_label)
        
        # Warning message
        warning_label = QLabel("⚠️ This will create NEW POSTS in the selected groups")
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #d63384; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(warning_label)
        
        # Template selection group
        template_group = QGroupBox("1. Select Template")
        template_layout = QFormLayout()
        template_group.setLayout(template_layout)
        
        self.template_combo = QComboBox()
        self.template_combo.currentTextChanged.connect(self.on_template_changed)
        template_layout.addRow("Template:", self.template_combo)
        
        # Template preview
        self.template_preview = QTextEdit()
        self.template_preview.setMaximumHeight(100)
        self.template_preview.setReadOnly(True)
        self.template_preview.setPlaceholderText("Select a template to see preview...")
        template_layout.addRow("Preview:", self.template_preview)
        
        layout.addWidget(template_group)
        
        # Groups selection group
        groups_group = QGroupBox("2. Target Facebook Groups")
        groups_layout = QVBoxLayout()
        groups_group.setLayout(groups_layout)
        
        # Group input area
        group_input_layout = QHBoxLayout()
        
        self.group_input = QLineEdit()
        self.group_input.setPlaceholderText("Enter Facebook group URL...")
        self.group_input.returnPressed.connect(self.add_group)
        group_input_layout.addWidget(self.group_input)
        
        add_group_button = QPushButton("Add Group")
        add_group_button.clicked.connect(self.add_group)
        group_input_layout.addWidget(add_group_button)
        
        groups_layout.addLayout(group_input_layout)
        
        # Groups list
        self.groups_list = QListWidget()
        self.groups_list.setMaximumHeight(150)
        groups_layout.addWidget(self.groups_list)
        
        # Group control buttons
        group_buttons_layout = QHBoxLayout()
        
        self.verify_button = QPushButton("🔍 Verify Membership")
        self.verify_button.clicked.connect(self.verify_groups)
        self.verify_button.setEnabled(False)
        group_buttons_layout.addWidget(self.verify_button)
        
        self.remove_group_button = QPushButton("🗑️ Remove Selected")
        self.remove_group_button.clicked.connect(self.remove_selected_group)
        self.remove_group_button.setEnabled(False)
        group_buttons_layout.addWidget(self.remove_group_button)
        
        # Clear all groups button
        clear_all_button = QPushButton("🗂️ Clear All")
        clear_all_button.clicked.connect(self.clear_all_groups)
        group_buttons_layout.addWidget(clear_all_button)
        
        group_buttons_layout.addStretch()
        
        groups_layout.addLayout(group_buttons_layout)
        
        # Saved groups section
        saved_groups_layout = QHBoxLayout()
        
        load_saved_button = QPushButton("📂 Load Previously Verified Groups")
        load_saved_button.clicked.connect(self.show_saved_groups_dialog)
        saved_groups_layout.addWidget(load_saved_button)
        
        saved_groups_layout.addStretch()
        
        groups_layout.addLayout(saved_groups_layout)
        
        layout.addWidget(groups_group)
        
        # Scheduling group
        schedule_group = QGroupBox("3. Posting Schedule")
        schedule_layout = QFormLayout()
        schedule_group.setLayout(schedule_layout)
        
        # Frequency setting
        frequency_layout = QHBoxLayout()
        
        self.frequency_spin = QSpinBox()
        self.frequency_spin.setRange(1, 168)  # 1 hour to 1 week
        self.frequency_spin.setValue(24)  # Default to once per day
        frequency_layout.addWidget(self.frequency_spin)
        
        frequency_layout.addWidget(QLabel("hours"))
        frequency_layout.addStretch()
        
        schedule_layout.addRow("Post every:", frequency_layout)
        
        # Start immediately checkbox
        self.start_immediately = QCheckBox("Start posting immediately")
        self.start_immediately.setChecked(True)
        schedule_layout.addWidget(self.start_immediately)
        
        layout.addWidget(schedule_group)
        
        # Summary group
        summary_group = QGroupBox("4. Summary")
        summary_layout = QVBoxLayout()
        summary_group.setLayout(summary_layout)
        
        self.summary_label = QLabel("Please configure the automation settings above.")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("color: #666; padding: 10px;")
        summary_layout.addWidget(self.summary_label)
        
        layout.addWidget(summary_group)
        
        # Button panel
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        button_layout.addStretch()
        
        self.create_button = QPushButton("✅ Create Automation")
        self.create_button.setDefault(True)
        self.create_button.clicked.connect(self.create_automation)
        self.create_button.setEnabled(False)
        button_layout.addWidget(self.create_button)
        
        layout.addLayout(button_layout)
        
        # Connect selection changes
        self.groups_list.itemSelectionChanged.connect(self.on_group_selection_changed)
        self.template_combo.currentTextChanged.connect(self.update_summary)
        self.frequency_spin.valueChanged.connect(self.update_summary)
        
        # Apply styles
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #4267B2;
            }
            QPushButton {
                background-color: #4267B2;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-weight: bold;
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
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
    
    def load_saved_verified_groups(self):
        """Load previously verified groups"""
        try:
            self.saved_verified_groups = self.file_manager.load_verified_groups()
            self.logger.info(f"Loaded {len(self.saved_verified_groups)} previously verified groups")
        except Exception as e:
            self.logger.error(f"Failed to load saved verified groups: {e}")
            self.saved_verified_groups = {}
    
    def show_saved_groups_dialog(self):
        """Show dialog to select from previously verified groups"""
        if not self.saved_verified_groups:
            QMessageBox.information(self, "No Saved Groups", 
                                  "No previously verified groups found.")
            return
        
        from PyQt5.QtWidgets import QCheckBox, QScrollArea, QWidget
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Previously Verified Groups")
        dialog.setGeometry(300, 300, 600, 400)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # Header
        header = QLabel("Select groups to add to your automation:")
        header.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Scroll area for checkboxes
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_widget.setLayout(scroll_layout)
        
        checkboxes = {}
        
        for group_url, group_data in self.saved_verified_groups.items():
            is_member = group_data.get('is_member', False)
            verified_date = group_data.get('verified_date', 'Unknown')
            
            # Extract group name from URL
            group_name = self.extract_group_name(group_url)
            
            # Create checkbox with status
            status_text = "✅ Member" if is_member else "❌ Not Member"
            checkbox_text = f"{group_name}\n{status_text} (Verified: {verified_date})"
            
            checkbox = QCheckBox(checkbox_text)
            checkbox.setEnabled(is_member)  # Only enable if user is a member
            checkboxes[group_url] = checkbox
            scroll_layout.addWidget(checkbox)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All Members")
        select_all_btn.clicked.connect(lambda: self.select_all_member_groups(checkboxes))
        button_layout.addWidget(select_all_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        load_btn = QPushButton("Load Selected")
        load_btn.clicked.connect(lambda: self.load_selected_groups(dialog, checkboxes))
        button_layout.addWidget(load_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def select_all_member_groups(self, checkboxes):
        """Select all groups where user is a member"""
        for group_url, checkbox in checkboxes.items():
            if checkbox.isEnabled():  # Only member groups are enabled
                checkbox.setChecked(True)
    
    def load_selected_groups(self, dialog, checkboxes):
        """Load selected groups from the dialog"""
        selected_groups = []
        
        for group_url, checkbox in checkboxes.items():
            if checkbox.isChecked():
                selected_groups.append(group_url)
        
        if selected_groups:
            # Add selected groups to the current list
            for group_url in selected_groups:
                if group_url not in self.group_urls:
                    self.group_urls.append(group_url)
                    
                    # Create list item with verification status
                    item = QListWidgetItem()
                    group_name = self.extract_group_name(group_url)
                    
                    # Get saved verification status
                    group_data = self.saved_verified_groups.get(group_url, {})
                    is_member = group_data.get('is_member', False)
                    verified_date = group_data.get('verified_date', 'Unknown')
                    
                    if is_member:
                        item.setText(f"✅ {group_name} (Verified: {verified_date})")
                        self.verified_groups[group_url] = True
                    else:
                        item.setText(f"❌ {group_name} (Not a member)")
                        self.verified_groups[group_url] = False
                    
                    item.setToolTip(group_url)
                    item.setData(Qt.UserRole, group_url)
                    self.groups_list.addItem(item)
            
            self.validate_form()
            self.update_summary()
            
            QMessageBox.information(self, "Groups Loaded", 
                                  f"Loaded {len(selected_groups)} groups successfully!")
        
        dialog.accept()
    
    def clear_all_groups(self):
        """Clear all groups from the list"""
        reply = QMessageBox.question(self, "Clear All Groups",
                                   "Are you sure you want to remove all groups?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.group_urls.clear()
            self.verified_groups.clear()
            self.groups_list.clear()
            self.verify_button.setEnabled(False)
            self.validate_form()
            self.update_summary()
    
    def load_templates(self):
        """Load available templates into combo box"""
        templates = self.template_manager.get_all_templates()
        
        self.template_combo.clear()
        self.template_combo.addItem("Select a template...", "")
        
        for template_id, template in templates.items():
            self.template_combo.addItem(template.name, template_id)
        
        if len(templates) == 0:
            self.template_combo.addItem("No templates available", "")
            self.template_combo.setEnabled(False)
    
    def on_template_changed(self):
        """Handle template selection change"""
        template_id = self.template_combo.currentData()
        
        if template_id:
            template = self.template_manager.get_template(template_id)
            if template:
                # Show preview (first 200 characters)
                preview_text = template.content
                if len(preview_text) > 200:
                    preview_text = preview_text[:200] + "..."
                
                self.template_preview.setPlainText(preview_text)
                
                # Add image info if present
                if template.images:
                    image_info = f"\n\n📷 Images: {len(template.images)} attached"
                    self.template_preview.append(image_info)
        else:
            self.template_preview.clear()
        
        self.validate_form()
        self.update_summary()
    
    def extract_group_name(self, group_url):
        """Extract group name from URL"""
        try:
            # Try to extract group name from URL
            parts = group_url.split('facebook.com/groups/')
            if len(parts) > 1:
                group_part = parts[1].split('/')[0].split('?')[0]
                # Convert URL-style name to readable format
                name = group_part.replace('-', ' ').replace('_', ' ').title()
                return name[:50]  # Limit length
        except Exception:
            pass
        
        return "Facebook Group"
    
    def remove_selected_group(self):
        """Remove selected group from the list"""
        current_item = self.groups_list.currentItem()
        if current_item:
            group_url = current_item.data(Qt.UserRole)
            if group_url in self.group_urls:
                self.group_urls.remove(group_url)
            
            if group_url in self.verified_groups:
                del self.verified_groups[group_url]
            
            row = self.groups_list.row(current_item)
            self.groups_list.takeItem(row)
        
        self.verify_button.setEnabled(len(self.group_urls) > 0)
        self.validate_form()
        self.update_summary()
    
    def on_group_selection_changed(self):
        """Handle group selection change"""
        has_selection = self.groups_list.currentItem() is not None
        self.remove_group_button.setEnabled(has_selection)
    
    def verify_groups(self):
        """Verify membership in all groups"""
        if not self.group_urls:
            return
        
        # Get group poster from parent (main window)
        try:
            main_window = self.parent()
            group_poster = main_window.group_poster
            
            # Disable button during verification
            self.verify_button.setEnabled(False)
            self.verify_button.setText("🔄 Verifying...")
            
            # Clear previous verification results
            self.verified_groups.clear()
            
            # Start verification worker
            self.verification_worker = GroupVerificationWorker(group_poster, self.group_urls)
            self.verification_worker.verification_complete.connect(self.on_group_verified)
            self.verification_worker.finished.connect(self.on_verification_finished)
            self.verification_worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Verification Error", 
                               f"Failed to start group verification: {str(e)}")
            self.verify_button.setEnabled(True)
            self.verify_button.setText("🔍 Verify Membership")
    
    def on_group_verified(self, group_url, is_member):
        """Handle individual group verification result"""
        self.verified_groups[group_url] = is_member
        
        # Save to persistent storage
        self.file_manager.add_verified_group(group_url, is_member)
        
        # Update list item
        for i in range(self.groups_list.count()):
            item = self.groups_list.item(i)
            if item.data(Qt.UserRole) == group_url:
                group_name = self.extract_group_name(group_url)
                current_time = time.strftime('%Y-%m-%d %H:%M')
                if is_member:
                    item.setText(f"✅ {group_name} (Verified: {current_time})")
                    item.setToolTip(f"{group_url}\nStatus: You are a member of this group")
                else:
                    item.setText(f"❌ {group_name} (Not a member)")
                    item.setToolTip(f"{group_url}\nStatus: You are NOT a member of this group")
                break
    
    def check_existing_verification(self, group_url):
        """Check if group was previously verified and still valid"""
        is_member, is_recent = self.file_manager.get_verified_group_status(group_url, max_age_hours=168)  # 7 days
        
        if is_recent and is_member is not None:
            self.verified_groups[group_url] = is_member
            return True
        return False
    
    def add_group(self):
        """Add a Facebook group to the list with enhanced verification check"""
        group_url = self.group_input.text().strip()
        
        if not group_url:
            return
        
        # Basic URL validation
        if not group_url.startswith(('http://', 'https://')):
            group_url = 'https://' + group_url
        
        if 'facebook.com/groups/' not in group_url:
            QMessageBox.warning(self, "Invalid URL", 
                              "Please enter a valid Facebook group URL.")
            return
        
        # Check for duplicates
        if group_url in self.group_urls:
            QMessageBox.information(self, "Duplicate Group", 
                                  "This group is already in the list.")
            return
        
        # Add to list
        self.group_urls.append(group_url)
        
        # Create list item
        item = QListWidgetItem()
        group_name = self.extract_group_name(group_url)
        item.setToolTip(group_url)
        item.setData(Qt.UserRole, group_url)
        
        # Check if previously verified
        if self.check_existing_verification(group_url):
            is_member = self.verified_groups[group_url]
            saved_data = self.saved_verified_groups.get(group_url, {})
            verified_date = saved_data.get('verified_date', 'Recently')
            
            if is_member:
                item.setText(f"✅ {group_name} (Verified: {verified_date})")
            else:
                item.setText(f"❌ {group_name} (Not a member)")
        else:
            item.setText(f"❓ {group_name} (Not verified)")
        
        self.groups_list.addItem(item)
        self.group_input.clear()
        
        self.verify_button.setEnabled(True)
        self.validate_form()
        self.update_summary()

    def on_verification_finished(self):
        """Handle verification completion"""
        self.verify_button.setEnabled(True)
        self.verify_button.setText("🔍 Verify Membership")
        
        # Check results
        member_count = sum(1 for is_member in self.verified_groups.values() if is_member)
        total_count = len(self.verified_groups)
        
        if member_count == 0:
            QMessageBox.warning(self, "No Group Membership", 
                              "You are not a member of any of the specified groups.\n"
                              "Please join the groups first or remove them from the list.")
        elif member_count < total_count:
            non_member_count = total_count - member_count
            QMessageBox.information(self, "Verification Complete", 
                                  f"Verification complete!\n"
                                  f"Member of: {member_count} groups\n"
                                  f"Not member of: {non_member_count} groups\n\n"
                                  f"Posts will only be created in groups where you are a member.")
        else:
            QMessageBox.information(self, "Verification Complete", 
                                  f"Great! You are a member of all {member_count} groups.")
        
        self.validate_form()
        self.update_summary()
    
    def validate_form(self):
        """Validate form and enable/disable create button"""
        template_selected = bool(self.template_combo.currentData())
        has_groups = len(self.group_urls) > 0
        has_verified_groups = any(self.verified_groups.get(url, False) for url in self.group_urls)
        
        is_valid = template_selected and has_groups and has_verified_groups
        self.create_button.setEnabled(is_valid)
    
    def update_summary(self):
        """Update the automation summary"""
        template_id = self.template_combo.currentData()
        frequency = self.frequency_spin.value()
        
        if not template_id or not self.group_urls:
            self.summary_label.setText("Please configure the automation settings above.")
            return
        
        template = self.template_manager.get_template(template_id)
        template_name = template.name if template else "Unknown"
        
        verified_groups = [url for url in self.group_urls if self.verified_groups.get(url, False)]
        
        summary = f"Automation Summary:\n\n"
        summary += f"• Template: {template_name}\n"
        summary += f"• Target Groups: {len(self.group_urls)} total"
        
        if self.verified_groups:
            summary += f" ({len(verified_groups)} verified as member)\n"
        else:
            summary += " (not verified)\n"
        
        summary += f"• Posting Frequency: Every {frequency} hours\n"
        
        if frequency == 24:
            summary += f"• Schedule: Once per day\n"
        elif frequency == 12:
            summary += f"• Schedule: Twice per day\n"
        elif frequency < 24:
            posts_per_day = 24 // frequency
            summary += f"• Schedule: {posts_per_day} times per day\n"
        else:
            days = frequency // 24
            summary += f"• Schedule: Once every {days} days\n"
        
        if verified_groups:
            summary += f"\n✅ Ready to create automation"
        else:
            summary += f"\n⚠️ Verify group membership before creating"
        
        self.summary_label.setText(summary)
    
    def create_automation(self):
        """Create the automation with better debugging"""
        template_id = self.template_combo.currentData()
        frequency = self.frequency_spin.value()
        start_immediately = self.start_immediately.isChecked()  # Get checkbox value
        
        # DEBUG: Log the checkbox value
        self.logger.info(f"DEBUG: Start immediately checkbox value: {start_immediately}")
        
        if not template_id:
            QMessageBox.warning(self, "No Template", "Please select a template.")
            return
        
        # Only include groups where user is verified as member
        verified_groups = [url for url in self.group_urls if self.verified_groups.get(url, False)]
        
        if not verified_groups:
            QMessageBox.warning(self, "No Valid Groups", 
                            "No groups where you are a verified member.\n"
                            "Please verify group membership first.")
            return
        
        try:
            # DEBUG: Log what we're about to create
            self.logger.info(f"DEBUG: Creating automation with start_immediately={start_immediately}")
            
            # Create the scheduled post
            post_id = self.scheduler.add_scheduled_post(
                template_id=template_id,
                group_urls=verified_groups,
                frequency_hours=frequency,
                start_immediately=start_immediately  # Pass the checkbox value
            )
            
            if post_id:
                template = self.template_manager.get_template(template_id)
                timing_msg = "immediately (within 1 minute)" if start_immediately else f"in {frequency} hours"
                
                # DEBUG: Show exactly what was scheduled
                scheduled_post = self.scheduler.scheduled_posts.get(post_id)
                if scheduled_post:
                    next_time = datetime.fromtimestamp(scheduled_post.next_post_time)
                    self.logger.info(f"DEBUG: Next post scheduled for: {next_time}")
                
                QMessageBox.information(self, "Automation Created", 
                                    f"Automation created successfully!\n\n"
                                    f"Template: {template.name}\n"
                                    f"Groups: {len(verified_groups)} groups\n"
                                    f"Frequency: Every {frequency} hours\n"
                                    f"First post: {timing_msg}\n\n"
                                    f"DEBUG: Next execution at {next_time.strftime('%H:%M:%S')}")
                self.accept()
            else:
                QMessageBox.critical(self, "Creation Failed", 
                                "Failed to create automation. Please try again.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

