"""
Template Editor - Post Template Creation and Editing Interface
Create and modify post templates with text content and image attachments
"""

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QPushButton, QListWidget,
                             QListWidgetItem, QFileDialog, QMessageBox,
                             QGroupBox, QFormLayout, QSplitter, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon

class TemplateEditorDialog(QDialog):
    def __init__(self, template_manager, template_id=None, parent=None):
        super().__init__(parent)
        self.template_manager = template_manager
        self.template_id = template_id
        self.template = None
        self.image_paths = []
        
        if template_id:
            self.template = template_manager.get_template(template_id)
            if self.template:
                self.image_paths = self.template.images.copy()
        
        self.init_ui()
        self.load_template_data()
    
    def init_ui(self):
        """Initialize template editor UI"""
        title = "Edit Template" if self.template_id else "Create New Template"
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 800, 600)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_label = QLabel(f"📝 {title}")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(header_label)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Template details
        left_panel = self.create_template_details_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Images
        right_panel = self.create_images_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([500, 300])
        
        # Button panel
        button_layout = QHBoxLayout()
        
        # Preview button
        self.preview_button = QPushButton("👁️ Preview")
        self.preview_button.clicked.connect(self.preview_template)
        button_layout.addWidget(self.preview_button)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # Save button
        self.save_button = QPushButton("💾 Save Template")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.save_template)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        # Apply styles
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QLineEdit, QTextEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus, QTextEdit:focus {
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
    
    def create_template_details_panel(self):
        """Create left panel with template details"""
        widget = QFrame()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Template details group
        details_group = QGroupBox("Template Details")
        details_layout = QFormLayout()
        details_group.setLayout(details_layout)
        
        # Template name
        self.name_field = QLineEdit()
        self.name_field.setPlaceholderText("Enter template name...")
        self.name_field.textChanged.connect(self.validate_form)
        details_layout.addRow("Template Name:", self.name_field)
        
        layout.addWidget(details_group)
        
        # Content group
        content_group = QGroupBox("Post Content")
        content_layout = QVBoxLayout()
        content_group.setLayout(content_layout)
        
        # Content text area
        self.content_field = QTextEdit()
        self.content_field.setPlaceholderText("Enter your post content here...\n\n"
                                            "Tips:\n"
                                            "• Write engaging content that will interest your audience\n"
                                            "• Use emojis to make posts more visually appealing\n"
                                            "• Keep it concise but informative\n"
                                            "• Remember this creates NEW POSTS, not comments")
        self.content_field.textChanged.connect(self.validate_form)
        self.content_field.setMinimumHeight(300)
        content_layout.addWidget(self.content_field)
        
        # Character count
        self.char_count_label = QLabel("0 characters")
        self.char_count_label.setStyleSheet("color: #666; font-size: 12px;")
        self.char_count_label.setAlignment(Qt.AlignRight)
        content_layout.addWidget(self.char_count_label)
        
        # Connect character counting
        self.content_field.textChanged.connect(self.update_char_count)
        
        layout.addWidget(content_group)
        
        return widget
    
    def create_images_panel(self):
        """Create right panel for image management"""
        widget = QFrame()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Images group
        images_group = QGroupBox("Image Attachments")
        images_layout = QVBoxLayout()
        images_group.setLayout(images_layout)
        
        # Image list
        self.images_list = QListWidget()
        self.images_list.setMaximumHeight(300)
        images_layout.addWidget(self.images_list)
        
        # Image control buttons
        image_buttons_layout = QHBoxLayout()
        
        add_image_button = QPushButton("📷 Add Images")
        add_image_button.clicked.connect(self.add_images)
        image_buttons_layout.addWidget(add_image_button)
        
        self.remove_image_button = QPushButton("🗑️ Remove")
        self.remove_image_button.clicked.connect(self.remove_selected_image)
        self.remove_image_button.setEnabled(False)
        image_buttons_layout.addWidget(self.remove_image_button)
        
        images_layout.addLayout(image_buttons_layout)
        
        # Connect selection change
        self.images_list.itemSelectionChanged.connect(self.on_image_selection_changed)
        
        layout.addWidget(images_group)
        
        # Tips group
        tips_group = QGroupBox("💡 Tips")
        tips_layout = QVBoxLayout()
        tips_group.setLayout(tips_layout)
        
        tips_text = QLabel("• Supported formats: JPG, PNG, GIF\n"
                          "• Maximum file size: 10MB per image\n"
                          "• Recommended: 1200x630 pixels\n"
                          "• Multiple images will create a gallery")
        tips_text.setWordWrap(True)
        tips_text.setStyleSheet("color: #666; font-size: 12px;")
        tips_layout.addWidget(tips_text)
        
        layout.addWidget(tips_group)
        layout.addStretch()
        
        return widget
    
    def load_template_data(self):
        """Load existing template data for editing"""
        if self.template:
            self.name_field.setText(self.template.name)
            self.content_field.setPlainText(self.template.content)
            
            # Load images
            for image_path in self.template.images:
                self.add_image_to_list(image_path)
            
            self.validate_form()
    
    def add_images(self):
        """Add images to the template"""
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp);;All Files (*)"
        )
        
        for file_path in file_paths:
            if file_path and file_path not in self.image_paths:
                # Check file size (10MB limit)
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:  # 10MB
                    QMessageBox.warning(self, "File Too Large",
                                      f"Image {os.path.basename(file_path)} is larger than 10MB and will be skipped.")
                    continue
                
                self.image_paths.append(file_path)
                self.add_image_to_list(file_path)
        
        self.validate_form()
    
    def add_image_to_list(self, image_path):
        """Add image to the list widget"""
        item = QListWidgetItem()
        item.setText(os.path.basename(image_path))
        item.setToolTip(image_path)
        item.setData(Qt.UserRole, image_path)
        
        # Try to set thumbnail
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to thumbnail size
                thumbnail = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                item.setIcon(QIcon(thumbnail))
        except Exception:
            pass  # Use default icon if thumbnail fails
        
        self.images_list.addItem(item)
    
    def remove_selected_image(self):
        """Remove selected image from the list"""
        current_item = self.images_list.currentItem()
        if current_item:
            image_path = current_item.data(Qt.UserRole)
            if image_path in self.image_paths:
                self.image_paths.remove(image_path)
            
            row = self.images_list.row(current_item)
            self.images_list.takeItem(row)
        
        self.validate_form()
    
    def on_image_selection_changed(self):
        """Handle image selection change"""
        has_selection = self.images_list.currentItem() is not None
        self.remove_image_button.setEnabled(has_selection)
    
    def update_char_count(self):
        """Update character count display"""
        content = self.content_field.toPlainText()
        char_count = len(content)
        self.char_count_label.setText(f"{char_count} characters")
        
        # Change color based on length
        if char_count > 2000:
            self.char_count_label.setStyleSheet("color: red; font-size: 12px;")
        elif char_count > 1500:
            self.char_count_label.setStyleSheet("color: orange; font-size: 12px;")
        else:
            self.char_count_label.setStyleSheet("color: #666; font-size: 12px;")
    
    def validate_form(self):
        """Validate form and enable/disable save button"""
        name = self.name_field.text().strip()
        content = self.content_field.toPlainText().strip()
        
        is_valid = len(name) > 0 and len(content) > 0
        self.save_button.setEnabled(is_valid)
    
    def preview_template(self):
        """Show template preview"""
        name = self.name_field.text().strip()
        content = self.content_field.toPlainText().strip()
        
        if not name or not content:
            QMessageBox.warning(self, "Incomplete Template",
                              "Please fill in template name and content before previewing.")
            return
        
        preview_text = f"Template: {name}\n"
        preview_text += "="*50 + "\n\n"
        preview_text += content
        
        if self.image_paths:
            preview_text += f"\n\n📷 Images ({len(self.image_paths)}):\n"
            for i, image_path in enumerate(self.image_paths, 1):
                preview_text += f"{i}. {os.path.basename(image_path)}\n"
        
        QMessageBox.information(self, "Template Preview", preview_text)
    
    def save_template(self):
        """Save the template"""
        name = self.name_field.text().strip()
        content = self.content_field.toPlainText().strip()
        
        if not name or not content:
            QMessageBox.warning(self, "Incomplete Template",
                              "Please fill in all required fields.")
            return
        
        try:
            if self.template_id:
                # Update existing template
                success = self.template_manager.update_template(
                    self.template_id, name, content, self.image_paths
                )
                if success:
                    QMessageBox.information(self, "Success", "Template updated successfully!")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to update template.")
            else:
                # Create new template
                template_id = self.template_manager.create_template(name, content, self.image_paths)
                if template_id:
                    QMessageBox.information(self, "Success", "Template created successfully!")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to create template.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
