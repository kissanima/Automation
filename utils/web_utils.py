"""
WebDriver utilities - Profile copy approach
"""

import time
import random
import logging
import os
import platform
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class WebDriverManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.automation_profile_path = None
    
    def get_chrome_profile_path(self):
        """Get the default Chrome profile path"""
        system = platform.system()
        
        if system == "Windows":
            return os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
        elif system == "Darwin":  # macOS
            return os.path.expanduser("~/Library/Application Support/Google/Chrome")
        else:  # Linux
            return os.path.expanduser("~/.config/google-chrome")
    
    def create_automation_profile(self):
        """Create a copy of Chrome profile for automation use"""
        try:
            original_profile = self.get_chrome_profile_path()
            if not original_profile or not os.path.exists(original_profile):
                self.logger.error("Original Chrome profile not found")
                return None
            
            # Create automation profile directory
            automation_dir = os.path.join(os.getcwd(), "chrome_automation_profile")
            
            # Only copy if it doesn't exist or is older than 7 days
            should_copy = True
            if os.path.exists(automation_dir):
                # Check age of automation profile
                profile_age = time.time() - os.path.getmtime(automation_dir)
                if profile_age < 7 * 24 * 3600:  # 7 days
                    should_copy = False
                    self.logger.info("Using existing automation profile (less than 7 days old)")
            
            if should_copy:
                self.logger.info("Creating/updating automation profile copy...")
                
                # Remove old automation profile if exists
                if os.path.exists(automation_dir):
                    shutil.rmtree(automation_dir)
                
                # Copy important parts of the profile
                os.makedirs(automation_dir, exist_ok=True)
                
                # Copy essential files/folders
                essential_items = [
                    "Default/Cookies",
                    "Default/Login Data",
                    "Default/Preferences",
                    "Default/Local State",
                    "Default/Web Data",
                    "Local State"
                ]
                
                for item in essential_items:
                    src_path = os.path.join(original_profile, item)
                    dst_path = os.path.join(automation_dir, item)
                    
                    if os.path.exists(src_path):
                        try:
                            # Create directory structure
                            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                            
                            if os.path.isfile(src_path):
                                shutil.copy2(src_path, dst_path)
                            else:
                                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                            
                            self.logger.debug(f"Copied {item}")
                        except Exception as e:
                            self.logger.warning(f"Failed to copy {item}: {e}")
                
                self.logger.info("Automation profile copy created successfully")
            
            self.automation_profile_path = automation_dir
            return automation_dir
            
        except Exception as e:
            self.logger.error(f"Failed to create automation profile: {e}")
            return None
    
    def get_driver(self, user_agent=None, use_existing_profile=True):
        """Create WebDriver with dedicated automation profile"""
        options = Options()
        
        if use_existing_profile:
            # Create automation profile copy
            profile_path = self.create_automation_profile()
            
            if profile_path:
                options.add_argument(f"--user-data-dir={profile_path}")
                options.add_argument("--profile-directory=Default")
                self.logger.info(f"Using automation profile: {profile_path}")
            else:
                self.logger.warning("Failed to create automation profile, using clean session")
        
        # Anti-detection options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        
        # Remove automation indicators
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Realistic user agent
        if user_agent:
            options.add_argument(f'--user-agent={user_agent}')
        else:
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional stealth options
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        
        try:
            driver = webdriver.Chrome(options=options)
            
            # Anti-detection scripts
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            
            # Set realistic window size
            driver.set_window_size(1366, 768)
            
            self.logger.info("WebDriver created with automation profile")
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to create WebDriver: {e}")
            return None
    
    def cleanup_automation_profile(self):
        """Clean up automation profile if needed"""
        try:
            if self.automation_profile_path and os.path.exists(self.automation_profile_path):
                # Only clean if older than 30 days
                profile_age = time.time() - os.path.getmtime(self.automation_profile_path)
                if profile_age > 30 * 24 * 3600:  # 30 days
                    shutil.rmtree(self.automation_profile_path)
                    self.logger.info("Cleaned up old automation profile")
        except Exception as e:
            self.logger.error(f"Failed to cleanup automation profile: {e}")
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def human_type(self, element, text, speed='normal'):
        """Type text with adjustable speed and human-like behavior"""
        
        # Speed configurations
        speed_configs = {
            'slow': {
                'char_delay_min': 0.08,
                'char_delay_max': 0.20,
                'pause_chance': 0.15,  # 15% chance of longer pause
                'pause_min': 0.5,
                'pause_max': 1.0
            },
            'normal': {
                'char_delay_min': 0.05,
                'char_delay_max': 0.15,
                'pause_chance': 0.10,  # 10% chance of longer pause
                'pause_min': 0.3,
                'pause_max': 0.8
            },
            'fast': {
                'char_delay_min': 0.02,
                'char_delay_max': 0.08,
                'pause_chance': 0.05,  # 5% chance of longer pause
                'pause_min': 0.1,
                'pause_max': 0.3
            },
            'very_fast': {
                'char_delay_min': 0.01,
                'char_delay_max': 0.04,
                'pause_chance': 0.02,  # 2% chance of longer pause
                'pause_min': 0.05,
                'pause_max': 0.15
            },
            'instant': {
                'char_delay_min': 0.005,
                'char_delay_max': 0.015,
                'pause_chance': 0.01,  # 1% chance of longer pause
                'pause_min': 0.02,
                'pause_max': 0.05
            }
        }
        
        config = speed_configs.get(speed, speed_configs['normal'])
        
        for char in text:
            element.send_keys(char)
            
            # Random delay between characters
            time.sleep(random.uniform(config['char_delay_min'], config['char_delay_max']))
            
            # Occasional longer pause (like humans do)
            if random.random() < config['pause_chance']:
                time.sleep(random.uniform(config['pause_min'], config['pause_max']))

    
    def smooth_scroll(self, driver, pixels):
        """Smooth scrolling"""
        current_position = driver.execute_script("return window.pageYOffset;")
        target_position = current_position + pixels
        
        step_size = 50
        steps = abs(pixels) // step_size
        
        for i in range(steps):
            if pixels > 0:
                driver.execute_script(f"window.scrollTo(0, {current_position + (i + 1) * step_size});")
            else:
                driver.execute_script(f"window.scrollTo(0, {current_position - (i + 1) * step_size});")
            time.sleep(0.1)
        
        driver.execute_script(f"window.scrollTo(0, {target_position});")
