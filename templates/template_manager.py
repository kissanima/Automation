"""
Template Management System
Handles creation, editing, and storage of post templates
"""

import json
import time
import uuid
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from utils.file_manager import FileManager

@dataclass
class PostTemplate:
    id: str
    name: str
    content: str
    images: List[str]
    created_at: float
    modified_at: float
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()
        if not self.modified_at:
            self.modified_at = time.time()

class TemplateManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.file_manager = FileManager()
        self.templates: Dict[str, PostTemplate] = {}
        self.load_templates()
    
    def create_template(self, name: str, content: str, images: List[str] = None) -> str:
        """Create a new post template"""
        if images is None:
            images = []
        
        template_id = str(uuid.uuid4())
        template = PostTemplate(
            id=template_id,
            name=name,
            content=content,
            images=images,
            created_at=time.time(),
            modified_at=time.time()
        )
        
        self.templates[template_id] = template
        self.save_templates()
        
        self.logger.info(f"Created template: {name} ({template_id})")
        return template_id
    
    def update_template(self, template_id: str, name: str = None, 
                       content: str = None, images: List[str] = None) -> bool:
        """Update an existing template"""
        if template_id not in self.templates:
            self.logger.error(f"Template not found: {template_id}")
            return False
        
        template = self.templates[template_id]
        
        if name is not None:
            template.name = name
        if content is not None:
            template.content = content
        if images is not None:
            template.images = images
        
        template.modified_at = time.time()
        
        self.save_templates()
        self.logger.info(f"Updated template: {template_id}")
        return True
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template"""
        if template_id not in self.templates:
            self.logger.error(f"Template not found: {template_id}")
            return False
        
        del self.templates[template_id]
        self.save_templates()
        
        self.logger.info(f"Deleted template: {template_id}")
        return True
    
    def get_template(self, template_id: str) -> Optional[PostTemplate]:
        """Get a specific template"""
        return self.templates.get(template_id)
    
    def get_all_templates(self) -> Dict[str, PostTemplate]:
        """Get all templates"""
        return self.templates.copy()
    
    def get_template_names(self) -> Dict[str, str]:
        """Get template ID to name mapping"""
        return {tid: template.name for tid, template in self.templates.items()}
    
    def save_templates(self):
        """Save templates to file"""
        try:
            data = {}
            for template_id, template in self.templates.items():
                data[template_id] = asdict(template)
            
            self.file_manager.save_templates(data)
            
        except Exception as e:
            self.logger.error(f"Failed to save templates: {e}")
    
    def load_templates(self):
        """Load templates from file"""
        try:
            data = self.file_manager.load_templates()
            
            for template_id, template_data in data.items():
                template = PostTemplate(**template_data)
                self.templates[template_id] = template
            
            self.logger.info(f"Loaded {len(self.templates)} templates")
            
        except Exception as e:
            self.logger.error(f"Failed to load templates: {e}")
    
    def validate_template(self, template: PostTemplate) -> List[str]:
        """Validate template data and return list of issues"""
        issues = []
        
        if not template.name.strip():
            issues.append("Template name cannot be empty")
        
        if not template.content.strip():
            issues.append("Template content cannot be empty")
        
        # Validate image paths
        import os
        for image_path in template.images:
            if image_path and not os.path.exists(image_path):
                issues.append(f"Image file not found: {image_path}")
        
        return issues
