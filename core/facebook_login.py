"""
Facebook Login and Session Management - FIXED VERSION
Handles secure authentication, session persistence, and two-factor authentication
"""

import json
import time
import random
import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils.encryption import EncryptionManager
from utils.web_utils import WebDriverManager

class FacebookLogin:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encryption = EncryptionManager()
        self.web_manager = WebDriverManager()
        self.session_file = "data/session_data.enc"
        self.credentials_file = "data/credentials.enc"
        self.driver = None
        self.is_logged_in = False
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
    def save_credentials(self, username, password):
        """Securely save Facebook credentials"""
        try:
            credentials = {
                'username': username,
                'password': password
            }
            encrypted_data = self.encryption.encrypt(json.dumps(credentials))
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
            self.logger.info("Credentials saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save credentials: {e}")
            return False
    
    def load_credentials(self):
        """Load saved credentials"""
        try:
            if not os.path.exists(self.credentials_file):
                return None, None
                
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = self.encryption.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data)
            return credentials['username'], credentials['password']
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {e}")
            return None, None
    
    def save_session(self):
        """Save current browser session with better persistence"""
        try:
            if not self.driver:
                return False
            
            # Wait a moment to ensure all cookies are set
            time.sleep(2)
            
            # Get all cookies
            cookies = self.driver.get_cookies()
            
            # Get localStorage data
            local_storage = {}
            try:
                local_storage = self.driver.execute_script("return window.localStorage;")
            except Exception as e:
                self.logger.warning(f"Could not get localStorage: {e}")
            
            # Get sessionStorage data  
            session_storage = {}
            try:
                session_storage = self.driver.execute_script("return window.sessionStorage;")
            except Exception as e:
                self.logger.warning(f"Could not get sessionStorage: {e}")
            
            session_data = {
                'cookies': cookies,
                'local_storage': local_storage,
                'session_storage': session_storage,
                'current_url': self.driver.current_url,
                'user_agent': self.driver.execute_script("return navigator.userAgent;"),
                'timestamp': time.time()
            }
            
            encrypted_data = self.encryption.encrypt(json.dumps(session_data, default=str))
            with open(self.session_file, 'wb') as f:
                f.write(encrypted_data)
            
            self.logger.info("Session saved successfully with enhanced persistence")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
            return False
    
    def load_session(self):
        """Load and restore previous session with better persistence"""
        try:
            if not os.path.exists(self.session_file):
                return False
                
            with open(self.session_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.encryption.decrypt(encrypted_data)
            session_data = json.loads(decrypted_data)
            
            # Check if session is not too old (48 hours instead of 24)
            if time.time() - session_data['timestamp'] > 172800:  # 48 hours
                self.logger.info("Session expired, will need fresh login")
                return False
            
            # Initialize driver with same user agent
            self.driver = self.web_manager.get_driver(user_agent=session_data.get('user_agent'))
            
            # Navigate to Facebook first
            self.driver.get("https://www.facebook.com")
            time.sleep(3)
            
            # Restore cookies
            for cookie in session_data['cookies']:
                try:
                    # Ensure domain is set correctly
                    if 'domain' not in cookie or not cookie['domain']:
                        cookie['domain'] = '.facebook.com'
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    self.logger.warning(f"Failed to add cookie: {e}")
            
            # Restore localStorage
            if session_data.get('local_storage'):
                try:
                    for key, value in session_data['local_storage'].items():
                        self.driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")
                except Exception as e:
                    self.logger.warning(f"Failed to restore localStorage: {e}")
            
            # Restore sessionStorage
            if session_data.get('session_storage'):
                try:
                    for key, value in session_data['session_storage'].items():
                        self.driver.execute_script(f"window.sessionStorage.setItem('{key}', '{value}');")
                except Exception as e:
                    self.logger.warning(f"Failed to restore sessionStorage: {e}")
            
            # Navigate to Facebook again to apply session
            self.driver.refresh()
            time.sleep(5)
            
            # Check if still logged in
            if self.is_session_valid():
                self.is_logged_in = True
                self.logger.info("Session restored successfully")
                return True
            else:
                self.logger.info("Session invalid, will need fresh login")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to load session: {e}")
            return False
    
    def is_session_valid(self):
        """Enhanced session validation with better detection"""
        try:
            # Wait a bit for page to load completely
            self.web_manager.random_delay(2, 4)
            
            current_url = self.driver.current_url.lower()
            self.logger.info(f"Checking session validity on URL: {current_url}")
            
            # If we're on login page, definitely not logged in
            if any(page in current_url for page in ['login', 'checkpoint', 'recover']):
                self.logger.info("On login/checkpoint page - not logged in")
                return False
            
            # If we're on main Facebook domain, check for logged-in indicators
            if 'facebook.com' in current_url:
                wait = WebDriverWait(self.driver, 10)
                
                # Multiple strategies to detect logged-in state
                logged_in_indicators = [
                    # Strategy 1: Look for navigation elements
                    {
                        'selectors': [
                            "[data-testid='blue_bar_profile_link']",
                            "[aria-label='Your profile']",
                            "[data-testid='nav-user-profile-link']",
                            "a[href*='/me/']"
                        ],
                        'name': 'profile_links'
                    },
                    
                    # Strategy 2: Look for main navigation
                    {
                        'selectors': [
                            "[role='banner']",
                            "[data-testid='fb-header']",
                            "div[role='navigation']"
                        ],
                        'name': 'navigation'
                    },
                    
                    # Strategy 3: Look for post creation areas
                    {
                        'selectors': [
                            "[aria-placeholder*='Write something']",
                            "[aria-placeholder*=\"What's on your mind\"]",
                            "div[data-pagelet*='composer']"
                        ],
                        'name': 'post_composer'
                    },
                    
                    # Strategy 4: Look for home feed
                    {
                        'selectors': [
                            "[data-pagelet='FeedUnit']",
                            "[role='feed']",
                            "[data-testid='post_message']"
                        ],
                        'name': 'feed_content'
                    },
                    
                    # Strategy 5: Check for user menu/dropdown
                    {
                        'selectors': [
                            "[aria-label*='Account']",
                            "[aria-label*='Menu']",
                            "div[role='button'][aria-expanded]"
                        ],
                        'name': 'user_menu'
                    }
                ]
                
                # Try each strategy
                for strategy in logged_in_indicators:
                    try:
                        for selector in strategy['selectors']:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            visible_elements = [e for e in elements if e.is_displayed()]
                            
                            if visible_elements:
                                self.logger.info(f"Session valid - found {strategy['name']} indicator: {selector}")
                                return True
                                
                    except Exception as e:
                        self.logger.debug(f"Strategy {strategy['name']} failed: {e}")
                        continue
                
                # Strategy 6: Check page source for logged-in content
                try:
                    page_source = self.driver.page_source.lower()
                    logged_in_text_indicators = [
                        'data-testid="blue_bar_profile_link"',
                        'aria-label="your profile"',
                        'aria-placeholder="write something"',
                        '"is_logged_in":true',
                        'data-pagelet="feedunit"'
                    ]
                    
                    for indicator in logged_in_text_indicators:
                        if indicator in page_source:
                            self.logger.info(f"Session valid - found text indicator: {indicator}")
                            return True
                            
                except Exception as e:
                    self.logger.debug(f"Page source check failed: {e}")
                
                # Strategy 7: Check for absence of login elements
                try:
                    login_indicators = [
                        "input[name='email']",
                        "input[name='pass']",
                        "input[type='password']",
                        "[data-testid='royal_email']"
                    ]
                    
                    has_login_elements = False
                    for selector in login_indicators:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if any(e.is_displayed() for e in elements):
                            has_login_elements = True
                            break
                    
                    if not has_login_elements and 'facebook.com' in current_url:
                        self.logger.info("Session valid - no login elements found on Facebook domain")
                        return True
                        
                except Exception as e:
                    self.logger.debug(f"Login elements check failed: {e}")
            
            self.logger.warning("Could not determine session validity - assuming invalid")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking session validity: {e}")
            return False

    
    def wait_for_2fa_approval(self, max_wait_time=300):
        """Wait for 2FA approval (up to 5 minutes)"""
        self.logger.info("Waiting for 2FA approval...")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # Check if we've successfully logged in
                if self.is_session_valid():
                    self.logger.info("2FA approved, login successful")
                    return True
                
                # Check if there's an error or if we need to wait
                page_text = self.driver.page_source.lower()
                approval_indicators = [
                    "check your notifications",
                    "approve this login",
                    "another device",
                    "notification we sent",
                    "two-factor authentication",
                    "security check"
                ]
                
                if any(text in page_text for text in approval_indicators):
                    self.logger.info("Still waiting for 2FA approval...")
                    time.sleep(5)
                    continue
                
                # If we're here, check if we need to handle other cases
                time.sleep(3)
                
            except Exception as e:
                self.logger.warning(f"Error during 2FA wait: {e}")
                time.sleep(5)
        
        self.logger.error("2FA approval timeout")
        return False
    
    def login(self, username=None, password=None):
        """Enhanced login with pre-fill detection and proper driver management"""
        try:
            # Try to load existing session first
            if self.load_session():
                return True
            
            # IMPORTANT: Clean up failed session driver before creating new one
            if self.driver:
                self.logger.info("Cleaning up failed session driver")
                self.driver.quit()
                self.driver = None
            
            # Now initialize driver for fresh login
            self.logger.info("Creating new driver for fresh login")
            self.driver = self.web_manager.get_driver(use_existing_profile=True)
            
            # Navigate to Facebook first and check if already logged in
            self.logger.info("Checking if already logged in...")
            self.driver.get("https://www.facebook.com")
            self.web_manager.random_delay(3, 6)
            
            # Check if already logged in
            if self.is_session_valid():
                self.is_logged_in = True
                self.save_session()
                self.logger.info("Already logged in - profile session active")
                return True
            
            # Not logged in, check current page
            current_url = self.driver.current_url.lower()
            
            # If not on login page, navigate there
            if 'login' not in current_url:
                self.logger.info("Navigating to login page...")
                self.driver.get("https://www.facebook.com/login")
                self.web_manager.random_delay(3, 5)
            
            # Get credentials if not provided
            if not username or not password:
                username, password = self.load_credentials()
                if not username or not password:
                    self.logger.error("No credentials available for login")
                    return False
            
            # Check if login fields are pre-filled
            try:
                wait = WebDriverWait(self.driver, 15)
                
                # Find email field
                email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
                current_email = email_field.get_attribute('value') or ''
                
                # Find password field
                password_field = self.driver.find_element(By.ID, "pass")
                current_password = password_field.get_attribute('value') or ''
                
                self.logger.info(f"Email field content: {'[FILLED]' if current_email else '[EMPTY]'}")
                self.logger.info(f"Password field content: {'[FILLED]' if current_password else '[EMPTY]'}")
                
                # Fill email if empty or different
                if not current_email or current_email.lower() != username.lower():
                    self.logger.info("Filling email field...")
                    email_field.clear()
                    self.web_manager.random_delay(0.5, 1)
                    self.web_manager.human_type(email_field, username, speed='fast')
                else:
                    self.logger.info("Email field already correctly filled")
                
                self.web_manager.random_delay(1, 2)
                
                # Fill password if empty
                if not current_password:
                    self.logger.info("Filling password field...")
                    password_field.clear()
                    self.web_manager.random_delay(0.5, 1)
                    self.web_manager.human_type(password_field, password, speed='fast')
                else:
                    self.logger.info("Password field already filled")
                
                self.web_manager.random_delay(1, 2)
                
                # Click login button
                login_button = self.driver.find_element(By.NAME, "login")
                login_button.click()
                self.logger.info("Clicked login button")
                
                # Wait for login to process
                self.web_manager.random_delay(5, 8)
                
                # Check if login was successful
                if self.is_session_valid():
                    self.is_logged_in = True
                    self.save_session()
                    self.save_credentials(username, password)
                    self.logger.info("Login successful")
                    return True
                
                # Check for 2FA
                page_source = self.driver.page_source.lower()
                twofa_indicators = [
                    "check your notifications",
                    "approve this login",
                    "another device",
                    "notification we sent",
                    "two-factor authentication",
                    "security check"
                ]
                
                if any(indicator in page_source for indicator in twofa_indicators):
                    self.logger.info("2FA detected, waiting for approval...")
                    if self.wait_for_2fa_approval():
                        self.is_logged_in = True
                        self.save_session()
                        self.save_credentials(username, password)
                        self.logger.info("Login successful after 2FA")
                        return True
                    else:
                        self.logger.error("2FA approval failed or timed out")
                        return False
                
                # Check for other issues
                self.logger.error("Login failed - unknown reason")
                return False
                
            except Exception as e:
                self.logger.error(f"Login process failed: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False


    
    def logout(self):
        """Logout and cleanup"""
        try:
            if self.driver:
                self.driver.quit()
            self.is_logged_in = False
            
            # Remove saved session
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            
            self.logger.info("Logged out successfully")
        except Exception as e:
            self.logger.error(f"Error during logout: {e}")
    
    def get_driver(self):
        """Get the current WebDriver instance"""
        return self.driver
    
    def debug_current_state(self):
        """Debug method to check current browser state"""
        try:
            if not self.driver:
                self.logger.info("DEBUG: No driver initialized")
                return
            
            current_url = self.driver.current_url
            title = self.driver.title
            
            self.logger.info(f"DEBUG: Current URL: {current_url}")
            self.logger.info(f"DEBUG: Page title: {title}")
            
            # Check for various elements
            elements_to_check = [
                ("Email field", "input[name='email']"),
                ("Password field", "input[name='pass']"),
                ("Profile link", "[data-testid='blue_bar_profile_link']"),
                ("Navigation", "[role='banner']"),
                ("Post composer", "[aria-placeholder*='Write something']")
            ]
            
            for name, selector in elements_to_check:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    visible_count = len([e for e in elements if e.is_displayed()])
                    self.logger.info(f"DEBUG: {name}: {visible_count} visible elements")
                except Exception as e:
                    self.logger.info(f"DEBUG: {name}: Error checking - {e}")
            
        except Exception as e:
            self.logger.error(f"DEBUG: Error in debug_current_state: {e}")

