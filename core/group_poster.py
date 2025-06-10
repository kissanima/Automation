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
        FIXED: Enhanced dialog detection and timing for textbox discovery
        """
        try:
            if not self.fb_login.is_logged_in:
                self.logger.error("Not logged into Facebook")
                return False
            
            # Load settings safely
            try:
                from ui.settings_dialog import get_current_settings
                settings = get_current_settings()
            except ImportError:
                settings = {
                    'navigation_delay': 5,
                    'click_delay': 2,
                    'image_upload_delay': 5,
                    'typing_speed_preset': 'Fast',
                    'detailed_logging': False
                }
            
            nav_delay = settings.get('navigation_delay', 5)
            click_delay = settings.get('click_delay', 2)
            typing_speed = settings.get('typing_speed_preset', 'Fast').lower()
            detailed_logging = settings.get('detailed_logging', False)
            
            driver = self.fb_login.get_driver()
            
            # Navigate to the group
            self.logger.info(f"Navigating to group: {group_url}")
            driver.get(group_url)
            self.web_manager.random_delay(nav_delay, nav_delay + 2)
            
            # Scroll to ensure page is loaded
            self.web_manager.smooth_scroll(driver, 300)
            self.web_manager.random_delay(click_delay, click_delay + 2)
            
            # STEP 1: Find and click the "Write something..." button to open the dialog
            wait = WebDriverWait(driver, 20)
            
            # Look for the main "Write something..." trigger
            write_something_selectors = [
                "span.x1lliihq.x6ikm8r.x10wlt62.x1n2onr6",
                "[aria-placeholder='Write something...']",
                "[placeholder='Write something...']",
                "span:contains('Write something')",
                "div[aria-placeholder='Write something...']",
                "div[role='textbox'][aria-placeholder*='Write']",
                "[data-testid*='composer']",
                "[data-pagelet*='composer']"
            ]
            
            write_button = None
            for selector in write_something_selectors:
                try:
                    if ":contains(" in selector:
                        elements = driver.find_elements(By.XPATH, f"//span[contains(text(), 'Write something')]")
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
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
                self.web_manager.random_delay(click_delay/2, click_delay)
                write_button.click()
                self.logger.info("Clicked 'Write something...' button")
            except Exception:
                driver.execute_script("arguments[0].click();", write_button)
                self.logger.info("Used JavaScript to click 'Write something...' button")
            
            # ✅ STEP 2: Enhanced dialog detection with longer wait
            self.logger.info("🔍 Waiting for create post dialog to fully load...")
            self.web_manager.random_delay(click_delay + 2, click_delay + 4)  # Longer wait
            
            dialog_container = None
            
            # Try multiple approaches to find the dialog
            try:
                # Method 1: Look for dialog with aria-label
                dialog_selectors = [
                    "[aria-label='Create post'][role='dialog']",
                    "[aria-label*='Create'][role='dialog']",
                    "[role='dialog'][aria-modal='true']",
                    "[role='dialog']"
                ]
                
                for selector in dialog_selectors:
                    try:
                        dialogs = driver.find_elements(By.CSS_SELECTOR, selector)
                        for dialog in dialogs:
                            if dialog.is_displayed():
                                dialog_container = dialog
                                aria_label = dialog.get_attribute('aria-label') or 'No label'
                                self.logger.info(f"Found dialog with selector: {selector} (label: '{aria_label}')")
                                break
                        if dialog_container:
                            break
                    except Exception:
                        continue
                
                # Method 2: If no dialog found, try broader search
                if not dialog_container:
                    self.logger.info("🔍 Trying broader dialog search...")
                    
                    # Look for any recently appeared dialog-like container
                    potential_dialogs = driver.find_elements(By.CSS_SELECTOR, "div")
                    for div in potential_dialogs:
                        if div.is_displayed():
                            div_html = driver.execute_script("return arguments[0].innerHTML;", div)
                            if ('contenteditable="true"' in div_html and 
                                'role="textbox"' in div_html and
                                ('write something' in div_html.lower() or 'create a public post' in div_html.lower())):
                                dialog_container = div
                                self.logger.info("Found dialog via content search")
                                break
            
            except Exception as e:
                self.logger.error(f"Error finding dialog: {e}")
            
            if not dialog_container:
                self.logger.error("Could not find create post dialog")
                return False
            
            # ✅ STEP 3: Enhanced textbox search with your EXACT structure + additional wait
            self.logger.info("🔍 Waiting for textbox to appear in dialog...")
            self.web_manager.random_delay(1, 2)  # Additional wait for textbox to appear
            
            dialog_textbox = None
            
            try:
                self.logger.info("🔍 Searching for textbox using EXACT structure...")
                
                # Method 1: Use your EXACT class structure
                exact_class_selector = "div.xzsf02u.x1a2a7pz.x1n2onr6.x14wi4xw.x9f619.x1lliihq.x5yr21d.xh8yej3.notranslate[contenteditable='true'][role='textbox']"
                
                exact_textboxes = dialog_container.find_elements(By.CSS_SELECTOR, exact_class_selector)
                
                if detailed_logging:
                    self.logger.info(f"Found {len(exact_textboxes)} textboxes with exact classes")
                
                for textbox in exact_textboxes:
                    if textbox.is_displayed() and textbox.is_enabled():
                        placeholder = textbox.get_attribute('aria-placeholder') or ''
                        if ('write something' in placeholder.lower() or 'create a public post' in placeholder.lower()):
                            dialog_textbox = textbox
                            self.logger.info(f"✅ Found textbox with EXACT classes: '{placeholder}'")
                            break
                
                # Method 2: Simplified class approach
                if not dialog_textbox:
                    self.logger.info("🔍 Trying simplified class approach...")
                    
                    simplified_selector = "div.xzsf02u[contenteditable='true'][role='textbox']"
                    simplified_textboxes = dialog_container.find_elements(By.CSS_SELECTOR, simplified_selector)
                    
                    if detailed_logging:
                        self.logger.info(f"Found {len(simplified_textboxes)} textboxes with simplified classes")
                    
                    for textbox in simplified_textboxes:
                        if textbox.is_displayed() and textbox.is_enabled():
                            placeholder = textbox.get_attribute('aria-placeholder') or ''
                            data_lexical = textbox.get_attribute('data-lexical-editor') or ''
                            
                            is_valid = (
                                ('write something' in placeholder.lower() or 'create a public post' in placeholder.lower()) and
                                'comment' not in placeholder.lower() and
                                data_lexical == 'true'
                            )
                            
                            if is_valid:
                                dialog_textbox = textbox
                                self.logger.info(f"✅ Found textbox with simplified classes: '{placeholder}'")
                                break
                
                # Method 3: Basic contenteditable search
                if not dialog_textbox:
                    self.logger.info("🔍 Trying basic contenteditable search...")
                    
                    basic_textboxes = dialog_container.find_elements(By.CSS_SELECTOR, "div[contenteditable='true']")
                    
                    if detailed_logging:
                        self.logger.info(f"Found {len(basic_textboxes)} contenteditable divs")
                    
                    for textbox in basic_textboxes:
                        if textbox.is_displayed() and textbox.is_enabled():
                            placeholder = textbox.get_attribute('aria-placeholder') or ''
                            role = textbox.get_attribute('role') or ''
                            
                            is_valid = (
                                role == 'textbox' and
                                ('write something' in placeholder.lower() or 'create a public post' in placeholder.lower()) and
                                'comment' not in placeholder.lower()
                            )
                            
                            if is_valid:
                                dialog_textbox = textbox
                                self.logger.info(f"✅ Found textbox with basic search: '{placeholder}'")
                                break
                
                # Method 4: Global search if dialog search failed
                if not dialog_textbox:
                    self.logger.info("🔍 Trying global search as last resort...")
                    
                    global_textboxes = driver.find_elements(By.CSS_SELECTOR, "div.xzsf02u[contenteditable='true'][role='textbox']")
                    
                    if detailed_logging:
                        self.logger.info(f"Found {len(global_textboxes)} textboxes globally")
                    
                    for textbox in global_textboxes:
                        if textbox.is_displayed() and textbox.is_enabled():
                            placeholder = textbox.get_attribute('aria-placeholder') or ''
                            
                            # Check if it's recently appeared (likely the dialog textbox)
                            try:
                                is_in_viewport = driver.execute_script("""
                                    var rect = arguments[0].getBoundingClientRect();
                                    return rect.top >= 0 && rect.top < window.innerHeight;
                                """, textbox)
                                
                                is_valid = (
                                    is_in_viewport and
                                    ('write something' in placeholder.lower() or 'create a public post' in placeholder.lower()) and
                                    'comment' not in placeholder.lower()
                                )
                                
                                if is_valid:
                                    dialog_textbox = textbox
                                    self.logger.info(f"✅ Found textbox with global search: '{placeholder}'")
                                    break
                            except Exception:
                                continue
            
            except Exception as e:
                self.logger.error(f"Error in textbox search: {e}")
            
            # Enhanced debug information
            if not dialog_textbox:
                self.logger.error("❌ Could not find CREATE POST textbox")
                
                try:
                    # Debug: Check what's in the dialog
                    self.logger.error("🔍 ENHANCED DEBUG:")
                    
                    # Check all contenteditable divs in dialog
                    all_contenteditable = dialog_container.find_elements(By.CSS_SELECTOR, "div[contenteditable='true']")
                    self.logger.error(f"Found {len(all_contenteditable)} contenteditable divs in dialog")
                    
                    for i, div in enumerate(all_contenteditable[:5]):
                        if div.is_displayed():
                            placeholder = div.get_attribute('aria-placeholder') or 'No placeholder'
                            role = div.get_attribute('role') or 'No role'
                            classes = div.get_attribute('class') or 'No classes'
                            self.logger.error(f"  Div {i+1}: placeholder='{placeholder}', role='{role}'")
                            self.logger.error(f"    Classes: {classes[:80]}...")
                    
                    # Check specifically for role=textbox
                    textbox_divs = dialog_container.find_elements(By.CSS_SELECTOR, "[role='textbox']")
                    self.logger.error(f"Found {len(textbox_divs)} elements with role='textbox' in dialog")
                    
                    # Check for your exact classes
                    exact_class_divs = dialog_container.find_elements(By.CSS_SELECTOR, "div.xzsf02u")
                    self.logger.error(f"Found {len(exact_class_divs)} elements with 'xzsf02u' class in dialog")
                    
                except Exception as debug_e:
                    self.logger.error(f"Enhanced debug failed: {debug_e}")
                
                return False
            
            # ✅ Enhanced safety check
            try:
                final_placeholder = dialog_textbox.get_attribute('aria-placeholder') or ''
                final_role = dialog_textbox.get_attribute('role') or ''
                
                is_valid_textbox = (
                    ('write something' in final_placeholder.lower() or 'create a public post' in final_placeholder.lower()) and
                    final_role == 'textbox' and
                    'comment' not in final_placeholder.lower()
                )
                
                if not is_valid_textbox:
                    self.logger.error("❌ SAFETY CHECK FAILED!")
                    self.logger.error(f"   Placeholder: '{final_placeholder}'")
                    self.logger.error(f"   Role: '{final_role}'")
                    return False
                
                group_type = "Public Group" if 'create a public post' in final_placeholder.lower() else "Owned Group"
                self.logger.info(f"✅ SAFETY CHECK PASSED: Confirmed textbox ({group_type})")
                self.logger.info(f"   Placeholder: '{final_placeholder}'")
            
            except Exception as e:
                self.logger.error(f"Safety check failed: {e}")
                return False
            
            # STEP 4: Type content
            self.logger.info("Typing content in CREATE POST textbox")
            dialog_textbox.clear()
            self.web_manager.human_type(dialog_textbox, template['content'], speed=typing_speed)
            self.web_manager.random_delay(1, 2)
            
            # STEP 5: Handle image attachments directly (NO separate function needed)
            if template.get('images') and len(template['images']) > 0:
                valid_images = [img for img in template['images'] if img and os.path.exists(img)]
                if valid_images:
                    self.logger.info(f"Starting direct drag & drop upload of {len(valid_images)} images")
                    self.web_manager.random_delay(2, 3)  # Brief wait for dialog readiness
                    
                    success = self._direct_drag_drop_upload(driver, dialog_container, valid_images)
                    if not success:
                        self.logger.warning("Failed to attach some images")
                else:
                    self.logger.warning("No valid images found to attach")

            
            # STEP 6: Find and click Post button
            post_button_selectors = [
                "[aria-label='Post'][role='button']",
                "div[aria-label='Post'][role='button']",
                "[role='dialog'] [aria-label='Post']",
                "button[aria-label='Post']"
            ]
            
            post_button = None
            for selector in post_button_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if (element.is_displayed() and element.is_enabled() and 
                            'post' in (element.get_attribute('aria-label') or '').lower()):
                            post_button = element
                            self.logger.info(f"Found Post button with selector: {selector}")
                            break
                    if post_button:
                        break
                except Exception:
                    continue
            
            if not post_button:
                self.logger.error("Could not find Post button")
                return False
            
            # Click Post button
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", post_button)
                self.web_manager.random_delay(click_delay/2, click_delay)
                post_button.click()
                self.logger.info("Clicked Post button")
            except Exception:
                driver.execute_script("arguments[0].click();", post_button)
                self.logger.info("Used JavaScript to click Post button")
            
            # STEP 7: Wait for completion
            post_completion_delay = nav_delay + 1
            self.web_manager.random_delay(post_completion_delay, post_completion_delay + 3)
            
            try:
                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[aria-label='Create post'][role='dialog']")))
                self.logger.info(f"Successfully posted to group: {group_url}")
                return True
            except TimeoutException:
                self.logger.warning("Could not verify post creation, but likely successful")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to post to group {group_url}: {e}")
            return False







    
    



    def _direct_drag_drop_upload(self, driver, dialog_container, image_paths, settings=None):
        """Direct drag & drop upload after Photo/video button click"""
        try:
            # ✅ USE SETTINGS FOR DELAYS
            if settings is None:
                try:
                    from ui.settings_dialog import get_current_settings
                    settings = get_current_settings()
                except ImportError:
                    settings = {'image_upload_delay': 5, 'detailed_logging': False}
            
            image_delay = settings.get('image_upload_delay', 5)
            detailed_logging = settings.get('detailed_logging', False)
            
            self.logger.info("Starting direct drag & drop upload...")
            
            # Find the drag & drop area that appears after clicking Photo/video
            drop_zone = None
            drop_zone_selectors = [
                # Look for drag & drop area that appears
                "[aria-label*='drag']",
                "[aria-label*='drop']", 
                # Look for upload areas
                "[data-testid*='upload']",
                "[data-testid*='photo']",
                # General areas in dialog
                "[role='dialog'] div[role='button']",
                "[role='dialog']"  # Use dialog itself as fallback
            ]
            
            for selector in drop_zone_selectors:
                try:
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
                        
                        if detailed_logging:
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
                    
                    # ✅ USE SETTINGS FOR PROCESSING WAIT
                    self.web_manager.random_delay(image_delay, image_delay + 3)
                    
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
                    
                    if detailed_logging:
                        self.logger.info(f"Found {preview_count} image elements after drag & drop")
                    
                    # Look for upload progress or success indicators
                    success_indicators = [
                        "[aria-label*='upload']",
                        "[data-testid*='upload']"
                    ]
                    
                    upload_activity = False
                    for indicator in success_indicators:
                        try:
                            elements = dialog_container.find_elements(By.CSS_SELECTOR, indicator)
                            if elements:
                                upload_activity = True
                                if detailed_logging:
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

