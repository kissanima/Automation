"""
Template Manager Dialog - Manage Existing Templates
View, edit, delete, and organize post templates
"""

import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem,
                             QMessageBox, QGroupBox, QTextEdit, QSplitter,
                             QFrame, QHeaderView, QTableWidget, QTableWidgetItem,
                             QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap

class TemplateManagerDialog(QDialog):
    templates_changed = pyqtSignal()  # Signal when templates are modified
    
    def __init__(self, template_manager, parent=None):
        super().__init__(parent)
        self.template_manager = template_manager
        self.logger = logging.getLogger(__name__)
        self.selected_template_id = None
        
        self.init_ui()
        self.load_templates()
    
    def init_ui(self):
        """Initialize template manager UI"""
        self.setWindowTitle("Template Manager")
        self.setGeometry(200, 200, 900, 600)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_label = QLabel("📝 Template Manager")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(header_label)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Template list
        left_panel = self.create_template_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Template preview/details
        right_panel = self.create_template_details_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 500])
        
        # Button panel
        button_layout = QHBoxLayout()
        
        # New template button
        new_button = QPushButton("📝 New Template")
        new_button.clicked.connect(self.create_new_template)
        button_layout.addWidget(new_button)
        
        button_layout.addStretch()
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # Apply styles
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
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
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #e3f2fd;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
    
    def create_template_list_panel(self):
        """Create left panel with template list"""
        widget = QFrame()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Templates list group
        list_group = QGroupBox("Templates")
        list_layout = QVBoxLayout()
        list_group.setLayout(list_layout)
        
        # Templates table
        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(3)
        self.templates_table.setHorizontalHeaderLabels(["Name", "Created", "Images"])
        
        # Configure table
        header = self.templates_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        self.templates_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.templates_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.templates_table.itemSelectionChanged.connect(self.on_template_selected)
        
        list_layout.addWidget(self.templates_table)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.edit_button = QPushButton("✏️ Edit")
        self.edit_button.clicked.connect(self.edit_selected_template)
        self.edit_button.setEnabled(False)
        control_layout.addWidget(self.edit_button)
        
        self.duplicate_button = QPushButton("📋 Duplicate")
        self.duplicate_button.clicked.connect(self.duplicate_selected_template)
        self.duplicate_button.setEnabled(False)
        control_layout.addWidget(self.duplicate_button)
        
        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.clicked.connect(self.delete_selected_template)
        self.delete_button.setEnabled(False)
        control_layout.addWidget(self.delete_button)
        
        list_layout.addLayout(control_layout)
        
        layout.addWidget(list_group)
        
        return widget
    
    def create_template_details_panel(self):
        """Create right panel with template details"""
        widget = QFrame()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Template details group
        details_group = QGroupBox("Template Preview")
        details_layout = QVBoxLayout()
        details_group.setLayout(details_layout)
        
        # Template name
        self.template_name_label = QLabel("Select a template to view details")
        self.template_name_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        details_layout.addWidget(self.template_name_label)
        
        # Template content
        self.template_content = QTextEdit()
        self.template_content.setReadOnly(True)
        self.template_content.setPlaceholderText("Template content will appear here...")
        details_layout.addWidget(self.template_content)
        
        # Template stats
        self.template_stats = QLabel("")
        self.template_stats.setStyleSheet("color: #666; margin: 10px;")
        details_layout.addWidget(self.template_stats)
        
        layout.addWidget(details_group)
        
        return widget
    
    def load_templates(self):
        """Load templates into the table"""
        templates = self.template_manager.get_all_templates()
        
        self.templates_table.setRowCount(len(templates))
        
        for row, (template_id, template) in enumerate(templates.items()):
            # Template name
            name_item = QTableWidgetItem(template.name)
            name_item.setData(Qt.UserRole, template_id)
            self.templates_table.setItem(row, 0, name_item)
            
            # Created date
            created_date = datetime.fromtimestamp(template.created_at).strftime("%m/%d/%Y %H:%M")
            date_item = QTableWidgetItem(created_date)
            self.templates_table.setItem(row, 1, date_item)
            
            # Images count
            image_count = len(template.images) if template.images else 0
            images_item = QTableWidgetItem(f"{image_count} images")
            self.templates_table.setItem(row, 2, images_item)
    
    def on_template_selected(self):
        """Handle template selection change"""
        current_row = self.templates_table.currentRow()
        
        if current_row >= 0:
            # Get template ID from the name item
            name_item = self.templates_table.item(current_row, 0)
            if name_item:
                self.selected_template_id = name_item.data(Qt.UserRole)
                
                # Enable buttons
                self.edit_button.setEnabled(True)
                self.duplicate_button.setEnabled(True)
                self.delete_button.setEnabled(True)
                
                # Load template details
                self.load_template_details(self.selected_template_id)
        else:
            self.selected_template_id = None
            self.edit_button.setEnabled(False)
            self.duplicate_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.clear_template_details()
    
    def load_template_details(self, template_id):
        """Load and display template details"""
        template = self.template_manager.get_template(template_id)
        if template:
            # Update name
            self.template_name_label.setText(template.name)
            
            # Update content
            self.template_content.setPlainText(template.content)
            
            # Update stats
            char_count = len(template.content)
            image_count = len(template.images) if template.images else 0
            created_date = datetime.fromtimestamp(template.created_at).strftime("%B %d, %Y at %H:%M")
            
            stats_text = f"📝 {char_count} characters\n"
            stats_text += f"📷 {image_count} images\n"
            stats_text += f"📅 Created: {created_date}"
            
            if template.images:
                stats_text += f"\n\nImages:"
                for i, img_path in enumerate(template.images, 1):
                    img_name = os.path.basename(img_path)
                    stats_text += f"\n{i}. {img_name}"
            
            self.template_stats.setText(stats_text)
    
    def clear_template_details(self):
        """Clear template details display"""
        self.template_name_label.setText("Select a template to view details")
        self.template_content.clear()
        self.template_stats.clear()
    
    def create_new_template(self):
        """Create a new template"""
        from ui.template_editor import TemplateEditorDialog
        
        dialog = TemplateEditorDialog(self.template_manager, None, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_templates()
            self.templates_changed.emit()
    
    def edit_selected_template(self):
        """Edit the selected template"""
        if self.selected_template_id:
            from ui.template_editor import TemplateEditorDialog
            
            dialog = TemplateEditorDialog(self.template_manager, self.selected_template_id, self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_templates()
                self.load_template_details(self.selected_template_id)
                self.templates_changed.emit()
    
    def duplicate_selected_template(self):
        """Duplicate the selected template"""
        if self.selected_template_id:
            template = self.template_manager.get_template(self.selected_template_id)
            if template:
                # Create duplicate with modified name
                new_name = f"{template.name} (Copy)"
                new_template_id = self.template_manager.create_template(
                    new_name, 
                    template.content, 
                    template.images.copy() if template.images else []
                )
                
                if new_template_id:
                    self.load_templates()
                    self.templates_changed.emit()
                    QMessageBox.information(self, "Template Duplicated", 
                                          f"Template '{new_name}' created successfully!")
                else:
                    QMessageBox.critical(self, "Error", "Failed to duplicate template.")
    
    def delete_selected_template(self):
        """Delete the selected template"""
        if self.selected_template_id:
            template = self.template_manager.get_template(self.selected_template_id)
            if template:
                reply = QMessageBox.question(
                    self, 
                    "Delete Template",
                    f"Are you sure you want to delete the template '{template.name}'?\n\n"
                    "This action cannot be undone.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    if self.template_manager.delete_template(self.selected_template_id):
                        self.load_templates()
                        self.clear_template_details()
                        self.templates_changed.emit()
                        QMessageBox.information(self, "Template Deleted", 
                                              "Template deleted successfully!")
                    else:
                        QMessageBox.critical(self, "Error", "Failed to delete template.")
