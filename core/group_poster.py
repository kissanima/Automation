"""
Facebook Group Posting Automation - FIXED VERSION
Handles the actual posting of content to Facebook groups with proper dialog interaction
"""

import time
import random
import logging
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils.web_utils import WebDriverManager

class GroupPoster:
    def __init__(self, facebook_login):
        self.logger = logging.getLogger(__name__)
        self.fb_login = facebook_login
        self.web_manager = WebDriverManager()
        
    def post_to_group(self, group_url, template):
        """
        Create a new post in a Facebook group using the post creation dialog
        IMPORTANT: This creates NEW POSTS, never comments on existing posts
        """
        try:
            if not self.fb_login.is_logged_in:
                self.logger.error("Not logged into Facebook")
                return False
            
            # ✅ LOAD SETTINGS - This is what was missing!
            try:
                from ui.settings_dialog import get_current_settings
                settings = get_current_settings()
            except ImportError:
                # Fallback defaults if settings not available
                settings = {
                    'navigation_delay': 5,
                    'click_delay': 2,
                    'image_upload_delay': 5,
                    'typing_speed_preset': 'Fast',
                    'detailed_logging': False
                }
            
            # Get configurable delays from settings
            nav_delay = settings.get('navigation_delay', 5)
            click_delay = settings.get('click_delay', 2)
            typing_speed = settings.get('typing_speed_preset', 'Fast').lower()
            detailed_logging = settings.get('detailed_logging', False)
            
            if detailed_logging:
                self.logger.info(f"Posting with settings: nav_delay={nav_delay}s, click_delay={click_delay}s, typing={typing_speed}")
            
            driver = self.fb_login.get_driver()
            
            # Navigate to the group
            self.logger.info(f"Navigating to group: {group_url}")
            driver.get(group_url)
            
            # ✅ USE SETTINGS FOR NAVIGATION DELAY
            self.web_manager.random_delay(nav_delay, nav_delay + 2)
            
            # Scroll to ensure page is loaded
            self.web_manager.smooth_scroll(driver, 300)
            
            # ✅ USE SETTINGS FOR SCROLL DELAY
            self.web_manager.random_delay(click_delay, click_delay + 2)
            
            # STEP 1: Find and click the "Write something..." button to open the dialog
            wait = WebDriverWait(driver, 20)
            
            # Look for the main "Write something..." trigger
            write_something_selectors = [
                # The span you identified
                "span.x1lliihq.x6ikm8r.x10wlt62.x1n2onr6",
                
                # Alternative selectors for "Write something..."
                "[aria-placeholder='Write something...']",
                "[placeholder='Write something...']",
                "span:contains('Write something')",
                
                # Div that contains the placeholder
                "div[aria-placeholder='Write something...']",
                "div[role='textbox'][aria-placeholder*='Write']",
                
                # Broader selectors
                "[data-testid*='composer']",
                "[data-pagelet*='composer']"
            ]
            
            write_button = None
            for selector in write_something_selectors:
                try:
                    if ":contains(" in selector:
                        # Use XPath for text-based search
                        elements = driver.find_elements(By.XPATH, f"//span[contains(text(), 'Write something')]")
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Check if it's the right element
                            element_text = element.get_attribute('textContent') or ''
                            if 'write something' in element_text.lower() or element.get_attribute('aria-placeholder'):
                                write_button = element
                                self.logger.info(f"Found 'Write something' element with selector: {selector}")
                                break
                    
                    if write_button:
                        break
                        
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not write_button:
                self.logger.error("Could not find 'Write something...' button")
                return False
            
            # Click the "Write something..." button to open the dialog
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", write_button)
                
                # ✅ USE SETTINGS FOR CLICK DELAY
                self.web_manager.random_delay(click_delay/2, click_delay)
                write_button.click()
                self.logger.info("Clicked 'Write something...' button")
            except Exception:
                # Try JavaScript click if regular click fails
                driver.execute_script("arguments[0].click();", write_button)
                self.logger.info("Used JavaScript to click 'Write something...' button")
            
            # STEP 2: Wait for the post creation dialog to appear
            # ✅ USE SETTINGS FOR DIALOG WAIT
            self.web_manager.random_delay(click_delay, click_delay + 2)
            
            # Look for the dialog textbox that appears
            dialog_textbox_selectors = [
                # From the HTML you provided
                "div[contenteditable='true'][role='textbox'][aria-placeholder='Write something...']",
                "div[data-lexical-editor='true']",
                
                # Alternative selectors for the dialog
                "[aria-label='Create post'] [contenteditable='true']",
                "[role='dialog'] [contenteditable='true']",
                "[role='dialog'] [role='textbox']",
                
                # Broader dialog selectors
                "div[contenteditable='true'][aria-placeholder*='Write']",
                "div[contenteditable='true'][spellcheck='true']"
            ]
            
            dialog_textbox = None
            for selector in dialog_textbox_selectors:
                try:
                    elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            dialog_textbox = element
                            self.logger.info(f"Found dialog textbox with selector: {selector}")
                            break
                    if dialog_textbox:
                        break
                except TimeoutException:
                    continue
            
            if not dialog_textbox:
                self.logger.error("Could not find post creation dialog textbox")
                return False
            
            # STEP 3: Type the content in the dialog textbox
            self.logger.info("Typing content in dialog textbox")
            
            # Clear any existing content
            dialog_textbox.clear()
            
            # ✅ USE SETTINGS FOR TYPING SPEED
            self.web_manager.human_type(dialog_textbox, template['content'], speed=typing_speed)
            self.web_manager.random_delay(1, 2)
            
            # STEP 4: Handle image attachments if present
            if template.get('images') and len(template['images']) > 0:
                success = self._attach_images_to_dialog(driver, template['images'], settings)
                if not success:
                    self.logger.warning("Failed to attach some images")
            
            # STEP 5: Find and click the "Post" button in the dialog
            post_button_selectors = [
                # From the HTML you provided
                "[aria-label='Post'][role='button']",
                "div[aria-label='Post'][role='button']",
                
                # Alternative selectors
                "[role='dialog'] [aria-label='Post']",
                "[role='dialog'] button:contains('Post')",
                
                # Generic post button selectors
                "button[aria-label='Post']",
                "[data-testid*='post-button']"
            ]
            
            post_button = None
            for selector in post_button_selectors:
                try:
                    if ":contains(" in selector:
                        elements = driver.find_elements(By.XPATH, "//button[contains(text(), 'Post')] | //div[contains(text(), 'Post') and @role='button']")
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if (element.is_displayed() and element.is_enabled() and 
                            'post' in (element.get_attribute('aria-label') or element.get_attribute('textContent') or '').lower()):
                            post_button = element
                            self.logger.info(f"Found Post button with selector: {selector}")
                            break
                    if post_button:
                        break
                except Exception:
                    continue
            
            if not post_button:
                self.logger.error("Could not find Post button in dialog")
                return False
            
            # Click the Post button
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", post_button)
                
                # ✅ USE SETTINGS FOR CLICK DELAY
                self.web_manager.random_delay(click_delay/2, click_delay)
                post_button.click()
                self.logger.info("Clicked Post button")
            except Exception:
                driver.execute_script("arguments[0].click();", post_button)
                self.logger.info("Used JavaScript to click Post button")
            
            # STEP 6: Wait for post to be created and dialog to close
            # ✅ USE SETTINGS FOR POST COMPLETION WAIT
            post_completion_delay = nav_delay + 1  # Slightly longer than navigation
            self.web_manager.random_delay(post_completion_delay, post_completion_delay + 3)
            
            # Verify post was created by checking if dialog closed
            try:
                # Check if the dialog is no longer visible
                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[aria-label='Create post'][role='dialog']")))
                self.logger.info(f"Successfully posted to group: {group_url}")
                return True
            except TimeoutException:
                self.logger.warning("Could not verify post creation, but likely successful")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to post to group {group_url}: {e}")
            return False

    
    def _attach_images_to_dialog(self, driver, image_paths):
        """Attach images via drag & drop directly after Photo/video button (no file dialog)"""
        try:
            wait = WebDriverWait(driver, 15)
            
            # STEP 1: Find the create post dialog first
            dialog_container = None
            dialog_selectors = [
                "[aria-label='Create post'][role='dialog']",
                "[role='dialog']"
            ]
            
            for selector in dialog_selectors:
                try:
                    dialogs = driver.find_elements(By.CSS_SELECTOR, selector)
                    for dialog in dialogs:
                        if dialog.is_displayed():
                            dialog_container = dialog
                            self.logger.info("Found create post dialog")
                            break
                    if dialog_container:
                        break
                except Exception:
                    continue
            
            if not dialog_container:
                self.logger.error("Could not find create post dialog")
                return False
            
            # STEP 2: Find Photo/video button using working XPath
            self.logger.info("Looking for Photo/video button using working XPath...")
            
            photo_video_button = None
            try:
                xpath_selector = "//img[contains(@src, 'Ivw7nhRtXyo.png')]/ancestor::*[@role='button'][1]"
                elements = dialog_container.find_elements(By.XPATH, xpath_selector)
                
                if elements:
                    for element in elements:
                        if element.is_displayed():
                            photo_video_button = element
                            self.logger.info("Found Photo/video button via working XPath")
                            break
                            
            except Exception as e:
                self.logger.error(f"XPath photo button search failed: {e}")
            
            if not photo_video_button:
                self.logger.error("Could not find Photo/video button")
                return False
            
            # STEP 3: Click the Photo/video button
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", photo_video_button)
                self.web_manager.random_delay(1, 2)
                photo_video_button.click()
                self.logger.info("Clicked Photo/video button")
            except Exception:
                driver.execute_script("arguments[0].click();", photo_video_button)
                self.logger.info("Used JavaScript to click Photo/video button")
            
            # STEP 4: Wait for drag & drop area to appear (skip "Add photos/videos" click)
            self.web_manager.random_delay(3, 5)  # Wait for interface to load
            self.logger.info("Waiting for drag & drop area to appear...")
            
            # STEP 5: Go directly to drag & drop (NO file dialog opening)
            valid_images = [img for img in image_paths if img and os.path.exists(img)]
            if not valid_images:
                self.logger.warning("No valid images found to attach")
                return False
            
            self.logger.info(f"Starting direct drag & drop upload of {len(valid_images)} images")
            return self._direct_drag_drop_upload(driver, dialog_container, valid_images)
            
        except Exception as e:
            self.logger.error(f"Image attachment failed: {e}")
            return False

    def _direct_drag_drop_upload(self, driver, dialog_container, image_paths):
        """Direct drag & drop upload after Photo/video button click"""
        try:
            self.logger.info("Starting direct drag & drop upload...")
            
            # Find the drag & drop area that appears after clicking Photo/video
            drop_zone = None
            drop_zone_selectors = [
                # Look for drag & drop area that appears
                "[aria-label*='drag']",
                "[aria-label*='drop']", 
                "div:has-text('drag and drop')",
                "div:has-text('Add photos')",
                # Look for upload areas
                "[data-testid*='upload']",
                "[data-testid*='photo']",
                # General areas in dialog
                "[role='dialog'] div[role='button']",
                "[role='dialog']"  # Use dialog itself as fallback
            ]
            
            for selector in drop_zone_selectors:
                try:
                    if ":has-text(" in selector:
                        # Skip CSS4 selectors
                        continue
                        
                    elements = dialog_container.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            drop_zone = elem
                            self.logger.info(f"Found drop zone with selector: {selector}")
                            break
                    if drop_zone:
                        break
                except Exception:
                    continue
            
            # Use dialog as drop zone if nothing else found
            if not drop_zone:
                drop_zone = dialog_container
                self.logger.info("Using dialog container as drop zone")
            
            # Prepare files
            files_data = []
            for path in image_paths:
                if os.path.exists(path):
                    try:
                        with open(path, 'rb') as f:
                            content = f.read()
                        
                        file_ext = os.path.splitext(path)[1].lower()
                        if file_ext == '.png':
                            file_type = 'image/png'
                        elif file_ext in ['.jpg', '.jpeg']:
                            file_type = 'image/jpeg'
                        elif file_ext == '.gif':
                            file_type = 'image/gif'
                        elif file_ext == '.webp':
                            file_type = 'image/webp'
                        else:
                            file_type = 'image/jpeg'
                        
                        import base64
                        b64_content = base64.b64encode(content).decode('utf-8')
                        
                        files_data.append({
                            'name': os.path.basename(path),
                            'type': file_type,
                            'content': b64_content
                        })
                        self.logger.info(f"Prepared file: {os.path.basename(path)} ({file_type}, {len(content)} bytes)")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to prepare file {path}: {e}")
                        continue
            
            if not files_data:
                self.logger.error("No files could be prepared")
                return False
            
            # Enhanced drag & drop JavaScript with better targeting
            js_script = """
                var dropZone = arguments[0];
                var filesData = arguments[1];
                
                console.log('Direct drag & drop with', filesData.length, 'files on', dropZone.tagName);
                
                try {
                    var dataTransfer = new DataTransfer();
                    
                    // Create files
                    for (var i = 0; i < filesData.length; i++) {
                        var fileData = filesData[i];
                        
                        var byteCharacters = atob(fileData.content);
                        var byteNumbers = new Array(byteCharacters.length);
                        for (var j = 0; j < byteCharacters.length; j++) {
                            byteNumbers[j] = byteCharacters.charCodeAt(j);
                        }
                        var byteArray = new Uint8Array(byteNumbers);
                        var blob = new Blob([byteArray], { type: fileData.type });
                        var file = new File([blob], fileData.name, {
                            type: fileData.type,
                            lastModified: Date.now()
                        });
                        
                        dataTransfer.items.add(file);
                        console.log('Added file:', fileData.name);
                    }
                    
                    console.log('Created', dataTransfer.files.length, 'files');
                    
                    // Try multiple drop strategies
                    var strategies = [
                        function() {
                            // Strategy 1: Standard drag & drop events
                            dropZone.dispatchEvent(new DragEvent('dragenter', {
                                bubbles: true, cancelable: true, dataTransfer: dataTransfer
                            }));
                            
                            setTimeout(function() {
                                dropZone.dispatchEvent(new DragEvent('dragover', {
                                    bubbles: true, cancelable: true, dataTransfer: dataTransfer
                                }));
                                
                                setTimeout(function() {
                                    dropZone.dispatchEvent(new DragEvent('drop', {
                                        bubbles: true, cancelable: true, dataTransfer: dataTransfer
                                    }));
                                    console.log('Strategy 1: Standard drag & drop completed');
                                }, 100);
                            }, 100);
                        },
                        
                        function() {
                            // Strategy 2: Find and use file input
                            setTimeout(function() {
                                var fileInputs = document.querySelectorAll('input[type="file"]');
                                for (var k = 0; k < fileInputs.length; k++) {
                                    var input = fileInputs[k];
                                    var accept = input.accept || '';
                                    
                                    if (accept.includes('image') || accept.includes('*') || accept === '') {
                                        try {
                                            input.files = dataTransfer.files;
                                            input.dispatchEvent(new Event('change', { bubbles: true }));
                                            console.log('Strategy 2: File input method completed');
                                            break;
                                        } catch (e) {
                                            console.log('File input failed:', e);
                                        }
                                    }
                                }
                            }, 300);
                        },
                        
                        function() {
                            // Strategy 3: Try paste event
                            setTimeout(function() {
                                var pasteEvent = new ClipboardEvent('paste', {
                                    bubbles: true,
                                    cancelable: true,
                                    clipboardData: dataTransfer
                                });
                                dropZone.dispatchEvent(pasteEvent);
                                console.log('Strategy 3: Paste event completed');
                            }, 500);
                        }
                    ];
                    
                    // Execute all strategies
                    strategies.forEach(function(strategy, index) {
                        setTimeout(strategy, index * 100);
                    });
                    
                    return true;
                    
                } catch (e) {
                    console.error('Drag & drop error:', e);
                    return false;
                }
            """
            
            # Execute drag & drop
            try:
                result = driver.execute_script(js_script, drop_zone, files_data)
                
                if result:
                    self.logger.info(f"Direct drag & drop executed for {len(files_data)} files")
                    
                    # Wait longer for processing
                    self.web_manager.random_delay(5, 8)
                    
                    # Check for image previews or any indication of success
                    preview_count = 0
                    preview_selectors = [
                        "img[src*='blob:']",
                        "img[src*='scontent']",
                        "[data-testid*='image']",
                        "[aria-label*='image']",
                        "img[alt*='preview']",
                        # Look for any new images in dialog
                        "[role='dialog'] img"
                    ]
                    
                    for selector in preview_selectors:
                        try:
                            elements = dialog_container.find_elements(By.CSS_SELECTOR, selector)
                            visible_elements = [e for e in elements if e.is_displayed()]
                            preview_count += len(visible_elements)
                        except Exception:
                            continue
                    
                    self.logger.info(f"Found {preview_count} image elements after drag & drop")
                    
                    # Look for upload progress or success indicators
                    success_indicators = [
                        "[aria-label*='upload']",
                        "[data-testid*='upload']",
                        "div:contains('Uploading')",
                        "div:contains('Upload complete')"
                    ]
                    
                    upload_activity = False
                    for indicator in success_indicators:
                        try:
                            if ":contains(" in indicator:
                                continue
                            elements = dialog_container.find_elements(By.CSS_SELECTOR, indicator)
                            if elements:
                                upload_activity = True
                                self.logger.info(f"Found upload activity: {indicator}")
                                break
                        except Exception:
                            continue
                    
                    if preview_count > 0 or upload_activity:
                        self.logger.info("Direct drag & drop appears successful")
                        return True
                    else:
                        self.logger.warning("No clear indication of upload success")
                        return True  # Still return True to continue with posting
                    
                else:
                    self.logger.error("Drag & drop JavaScript failed")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Drag & drop execution error: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Direct drag & drop failed: {e}")
            return False







    
    def verify_group_membership(self, group_url):
        """Verify that the user is a member of the group"""
        try:
            if not self.fb_login.is_logged_in:
                self.logger.error("Not logged into Facebook")
                return False
            
            # ✅ LOAD SETTINGS
            try:
                from ui.settings_dialog import get_current_settings
                settings = get_current_settings()
                nav_delay = settings.get('navigation_delay', 5)
                detailed_logging = settings.get('detailed_logging', False)
            except ImportError:
                nav_delay = 5
                detailed_logging = False
            
            driver = self.fb_login.get_driver()
            self.logger.info(f"Verifying membership for: {group_url}")
            
            # Navigate to the group
            driver.get(group_url)
            
            # ✅ USE SETTINGS FOR NAVIGATION DELAY
            self.web_manager.random_delay(nav_delay, nav_delay + 2)
            
            # Wait for page to load completely
            wait = WebDriverWait(driver, 15)
            
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except TimeoutException:
                self.logger.error("Failed to load group page")
                return False
            
            # Scroll to ensure all content is loaded
            self.web_manager.smooth_scroll(driver, 500)
            
            # ✅ USE SETTINGS FOR SCROLL DELAY
            self.web_manager.random_delay(2, 3)
            
            # Check for "Write something..." (indicates membership)
            write_something_indicators = [
                "span:contains('Write something')",
                "[aria-placeholder='Write something']",
                "[placeholder='Write something']"
            ]
            
            for selector in write_something_indicators:
                try:
                    if ":contains(" in selector:
                        elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Write something')]")
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements and any(elem.is_displayed() for elem in elements):
                        if detailed_logging:
                            self.logger.info("Found 'Write something' - user IS a member")
                        else:
                            self.logger.info("User IS a member")
                        return True
                except Exception:
                    continue
            
            # Check for "Join" button (indicates NOT a member)
            join_indicators = driver.find_elements(By.XPATH, "//span[contains(text(), 'Join')] | //button[contains(text(), 'Join')]")
            if join_indicators and any(elem.is_displayed() for elem in join_indicators):
                self.logger.info("Found 'Join' button - user is NOT a member")
                return False
            
            # If unclear, assume not a member for safety
            self.logger.warning("Could not determine membership - assuming NOT a member")
            return False
            
        except Exception as e:
            self.logger.error(f"Error verifying group membership for {group_url}: {e}")
            return False

