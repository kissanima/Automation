"""
File management utilities for data persistence - UPDATED
"""

import json
import os
import time
import logging
from typing import Dict, Any

class FileManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_dir = "data"
        self.templates_file = os.path.join(self.data_dir, "templates.json")
        self.automations_file = os.path.join(self.data_dir, "automations.json")
        self.logs_file = os.path.join(self.data_dir, "post_logs.json")
        self.verified_groups_file = os.path.join(self.data_dir, "verified_groups.json")  # ADD THIS LINE
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
    
    def save_templates(self, templates: Dict[str, Any]):
        """Save templates to JSON file"""
        try:
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save templates: {e}")
            raise
    
    def load_templates(self) -> Dict[str, Any]:
        """Load templates from JSON file"""
        try:
            if os.path.exists(self.templates_file):
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load templates: {e}")
            return {}
    
    def save_automations(self, automations: Dict[str, Any]):
        """Save automation schedules to JSON file"""
        try:
            with open(self.automations_file, 'w', encoding='utf-8') as f:
                json.dump(automations, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save automations: {e}")
            raise
    
    def load_automations(self) -> Dict[str, Any]:
        """Load automation schedules from JSON file"""
        try:
            if os.path.exists(self.automations_file):
                with open(self.automations_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load automations: {e}")
            return {}
    
    def add_log_entry(self, log_entry: Dict[str, Any]):
        """Add a log entry to the post logs"""
        try:
            logs = self.load_logs()
            logs.append(log_entry)
            
            # Keep only last 1000 entries to prevent file from growing too large
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(self.logs_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to add log entry: {e}")
    
    def load_logs(self) -> list:
        """Load post execution logs"""
        try:
            if os.path.exists(self.logs_file):
                with open(self.logs_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            self.logger.error(f"Failed to load logs: {e}")
            return []
    
    def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get a specific template by ID"""
        templates = self.load_templates()
        return templates.get(template_id)
    
    # ADD THESE NEW METHODS FOR GROUP VERIFICATION:
    
    def save_verified_groups(self, verified_groups: Dict[str, Any]):
        """Save verified group results to JSON file"""
        try:
            with open(self.verified_groups_file, 'w', encoding='utf-8') as f:
                json.dump(verified_groups, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save verified groups: {e}")
            raise

    def load_verified_groups(self) -> Dict[str, Any]:
        """Load verified group results from JSON file"""
        try:
            if os.path.exists(self.verified_groups_file):
                with open(self.verified_groups_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load verified groups: {e}")
            return {}

    def add_verified_group(self, group_url: str, is_member: bool, timestamp: float = None):
        """Add a single verified group result"""
        try:
            if timestamp is None:
                timestamp = time.time()
            
            verified_groups = self.load_verified_groups()
            verified_groups[group_url] = {
                'is_member': is_member,
                'verified_at': timestamp,
                'verified_date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            }
            self.save_verified_groups(verified_groups)
            self.logger.info(f"Added verified group: {group_url} (member: {is_member})")
        except Exception as e:
            self.logger.error(f"Failed to add verified group: {e}")

    def get_verified_group_status(self, group_url: str, max_age_hours: int = 168) -> tuple:
        """Get verification status for a group (returns is_member, is_recent)"""
        try:
            verified_groups = self.load_verified_groups()
            if group_url not in verified_groups:
                return None, False
            
            group_data = verified_groups[group_url]
            verified_at = group_data.get('verified_at', 0)
            age_hours = (time.time() - verified_at) / 3600
            
            is_recent = age_hours <= max_age_hours
            is_member = group_data.get('is_member', False)
            
            self.logger.debug(f"Group {group_url}: member={is_member}, age={age_hours:.1f}h, recent={is_recent}")
            return is_member, is_recent
        except Exception as e:
            self.logger.error(f"Failed to get verified group status: {e}")
            return None, False
    
    def remove_verified_group(self, group_url: str):
        """Remove a verified group from storage"""
        try:
            verified_groups = self.load_verified_groups()
            if group_url in verified_groups:
                del verified_groups[group_url]
                self.save_verified_groups(verified_groups)
                self.logger.info(f"Removed verified group: {group_url}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove verified group: {e}")
            return False
    
    def get_verified_groups_count(self) -> Dict[str, int]:
        """Get count of verified groups by status"""
        try:
            verified_groups = self.load_verified_groups()
            member_count = sum(1 for data in verified_groups.values() if data.get('is_member', False))
            non_member_count = len(verified_groups) - member_count
            
            return {
                'total': len(verified_groups),
                'members': member_count,
                'non_members': non_member_count
            }
        except Exception as e:
            self.logger.error(f"Failed to get verified groups count: {e}")
            return {'total': 0, 'members': 0, 'non_members': 0}
    
    def cleanup_old_verified_groups(self, max_age_hours: int = 720):  # 30 days
        """Remove old verification results"""
        try:
            verified_groups = self.load_verified_groups()
            current_time = time.time()
            cleaned_groups = {}
            removed_count = 0
            
            for group_url, group_data in verified_groups.items():
                verified_at = group_data.get('verified_at', 0)
                age_hours = (current_time - verified_at) / 3600
                
                if age_hours <= max_age_hours:
                    cleaned_groups[group_url] = group_data
                else:
                    removed_count += 1
            
            if removed_count > 0:
                self.save_verified_groups(cleaned_groups)
                self.logger.info(f"Cleaned up {removed_count} old verified groups")
            
            return removed_count
        except Exception as e:
            self.logger.error(f"Failed to cleanup old verified groups: {e}")
            return 0
