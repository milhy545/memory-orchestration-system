#!/usr/bin/env python3
"""
Browser MCP Server - Web Browser Automation
Poskytuje AI kontrolu nad webovým prohlížečem pro automatizaci, testování, scraping
Inspirováno Browser MCP (browsermcp.io) ale implementováno v Pythonu
"""
import json
import sys
import os
import time
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Optional imports for browser automation
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from PIL import Image
    import io
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False

class BrowserMCPServer:
    def __init__(self):
        self.driver = None
        self.browser_type = "chrome"
        self.session_id = None
        self.page_history = []
        self.screenshots_dir = Path("/tmp/browser_mcp_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Browser automation settings
        self.default_timeout = 10
        self.implicit_wait = 5
        
    def get_tools(self):
        """Return available browser automation tools"""
        tools = [
            {
                "name": "browser_start",
                "description": "Start browser session",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "browser": {
                            "type": "string",
                            "enum": ["chrome", "firefox", "edge"],
                            "default": "chrome",
                            "description": "Browser to use"
                        },
                        "headless": {
                            "type": "boolean",
                            "default": False,
                            "description": "Run in headless mode"
                        },
                        "window_size": {
                            "type": "string",
                            "default": "1920,1080",
                            "description": "Window size (width,height)"
                        },
                        "user_data_dir": {
                            "type": "string",
                            "description": "User data directory (preserves login states)"
                        },
                        "disable_images": {
                            "type": "boolean",
                            "default": False,
                            "description": "Disable image loading for faster browsing"
                        }
                    }
                }
            },
            {
                "name": "browser_stop",
                "description": "Stop browser session",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "browser_navigate",
                "description": "Navigate to URL",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to navigate to"
                        },
                        "wait_for_load": {
                            "type": "boolean",
                            "default": True,
                            "description": "Wait for page to load completely"
                        }
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "browser_back",
                "description": "Navigate back in browser history",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "browser_forward",
                "description": "Navigate forward in browser history",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "browser_refresh",
                "description": "Refresh current page",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "browser_click",
                "description": "Click on element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector or XPath to element"
                        },
                        "selector_type": {
                            "type": "string",
                            "enum": ["css", "xpath", "id", "class", "name", "tag", "link_text", "partial_link_text"],
                            "default": "css",
                            "description": "Type of selector"
                        },
                        "wait_timeout": {
                            "type": "number",
                            "default": 10,
                            "description": "Seconds to wait for element"
                        },
                        "double_click": {
                            "type": "boolean",
                            "default": False,
                            "description": "Perform double click"
                        }
                    },
                    "required": ["selector"]
                }
            },
            {
                "name": "browser_type",
                "description": "Type text into element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector or XPath to input element"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text to type"
                        },
                        "selector_type": {
                            "type": "string",
                            "enum": ["css", "xpath", "id", "class", "name", "tag"],
                            "default": "css",
                            "description": "Type of selector"
                        },
                        "clear_first": {
                            "type": "boolean",
                            "default": True,
                            "description": "Clear existing text first"
                        },
                        "press_enter": {
                            "type": "boolean",
                            "default": False,
                            "description": "Press Enter after typing"
                        }
                    },
                    "required": ["selector", "text"]
                }
            },
            {
                "name": "browser_get_text",
                "description": "Get text content from element(s)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector or XPath"
                        },
                        "selector_type": {
                            "type": "string",
                            "enum": ["css", "xpath", "id", "class", "name", "tag"],
                            "default": "css",
                            "description": "Type of selector"
                        },
                        "multiple": {
                            "type": "boolean",
                            "default": False,
                            "description": "Get text from multiple elements"
                        },
                        "attribute": {
                            "type": "string",
                            "description": "Get specific attribute instead of text content"
                        }
                    },
                    "required": ["selector"]
                }
            },
            {
                "name": "browser_wait_for_element",
                "description": "Wait for element to appear/disappear",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector or XPath"
                        },
                        "selector_type": {
                            "type": "string",
                            "enum": ["css", "xpath", "id", "class", "name", "tag"],
                            "default": "css",
                            "description": "Type of selector"
                        },
                        "condition": {
                            "type": "string",
                            "enum": ["present", "visible", "clickable", "invisible"],
                            "default": "present",
                            "description": "Condition to wait for"
                        },
                        "timeout": {
                            "type": "number",
                            "default": 10,
                            "description": "Seconds to wait"
                        }
                    },
                    "required": ["selector"]
                }
            },
            {
                "name": "browser_scroll",
                "description": "Scroll page or element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "enum": ["up", "down", "left", "right", "top", "bottom"],
                            "default": "down",
                            "description": "Scroll direction"
                        },
                        "amount": {
                            "type": "number",
                            "default": 500,
                            "description": "Pixels to scroll (ignored for top/bottom)"
                        },
                        "element_selector": {
                            "type": "string",
                            "description": "Selector for element to scroll (defaults to page)"
                        }
                    }
                }
            },
            {
                "name": "browser_screenshot",
                "description": "Take screenshot of page or element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Screenshot filename (auto-generated if not provided)"
                        },
                        "element_selector": {
                            "type": "string",
                            "description": "CSS selector to screenshot specific element"
                        },
                        "full_page": {
                            "type": "boolean",
                            "default": False,
                            "description": "Capture full page height"
                        }
                    }
                }
            },
            {
                "name": "browser_execute_js",
                "description": "Execute JavaScript code",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "script": {
                            "type": "string",
                            "description": "JavaScript code to execute"
                        },
                        "arguments": {
                            "type": "array",
                            "description": "Arguments to pass to script"
                        }
                    },
                    "required": ["script"]
                }
            },
            {
                "name": "browser_get_page_source",
                "description": "Get current page HTML source",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "save_to_file": {
                            "type": "string",
                            "description": "Save source to file path"
                        }
                    }
                }
            },
            {
                "name": "browser_get_page_info",
                "description": "Get current page information",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "browser_switch_to_frame",
                "description": "Switch to iframe/frame",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "frame_selector": {
                            "type": "string",
                            "description": "Frame selector (or 'default' for main content)"
                        },
                        "frame_index": {
                            "type": "number",
                            "description": "Frame index (0-based)"
                        }
                    }
                }
            },
            {
                "name": "browser_switch_to_tab",
                "description": "Switch between browser tabs",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tab_index": {
                            "type": "number",
                            "description": "Tab index (0-based)"
                        },
                        "tab_handle": {
                            "type": "string",
                            "description": "Specific tab handle"
                        }
                    }
                }
            },
            {
                "name": "browser_hover",
                "description": "Hover over element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector or XPath"
                        },
                        "selector_type": {
                            "type": "string",
                            "enum": ["css", "xpath", "id", "class", "name", "tag"],
                            "default": "css",
                            "description": "Type of selector"
                        }
                    },
                    "required": ["selector"]
                }
            },
            {
                "name": "browser_drag_and_drop",
                "description": "Drag and drop element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source_selector": {
                            "type": "string",
                            "description": "Source element selector"
                        },
                        "target_selector": {
                            "type": "string",
                            "description": "Target element selector"
                        },
                        "selector_type": {
                            "type": "string",
                            "enum": ["css", "xpath", "id", "class", "name", "tag"],
                            "default": "css",
                            "description": "Type of selector"
                        }
                    },
                    "required": ["source_selector", "target_selector"]
                }
            },
            {
                "name": "browser_get_cookies",
                "description": "Get browser cookies",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "Filter cookies by domain"
                        }
                    }
                }
            },
            {
                "name": "browser_set_cookie",
                "description": "Set browser cookie",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Cookie name"
                        },
                        "value": {
                            "type": "string",
                            "description": "Cookie value"
                        },
                        "domain": {
                            "type": "string",
                            "description": "Cookie domain"
                        },
                        "path": {
                            "type": "string",
                            "default": "/",
                            "description": "Cookie path"
                        }
                    },
                    "required": ["name", "value"]
                }
            },
            {
                "name": "browser_wait_and_pause",
                "description": "Wait/pause for specified time",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "seconds": {
                            "type": "number",
                            "default": 1,
                            "description": "Seconds to wait"
                        }
                    }
                }
            }
        ]
        
        return tools
    
    def check_browser_status(self) -> bool:
        """Check if browser session is active"""
        if not self.driver:
            return False
        
        try:
            # Try to get current URL to test if browser is responsive
            self.driver.current_url
            return True
        except WebDriverException:
            return False
    
    def start_browser(self, browser: str = "chrome", headless: bool = False, window_size: str = "1920,1080",
                     user_data_dir: str = None, disable_images: bool = False) -> Dict:
        """Start browser session"""
        if not SELENIUM_AVAILABLE:
            return {"success": False, "error": "Selenium not available. Install with: pip install selenium"}
        
        if self.driver:
            return {"success": False, "error": "Browser session already active"}
        
        try:
            self.browser_type = browser
            width, height = map(int, window_size.split(','))
            
            if browser == "chrome":
                options = ChromeOptions()
                if headless:
                    options.add_argument("--headless")
                options.add_argument(f"--window-size={width},{height}")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                
                if user_data_dir:
                    options.add_argument(f"--user-data-dir={user_data_dir}")
                
                if disable_images:
                    prefs = {"profile.managed_default_content_settings.images": 2}
                    options.add_experimental_option("prefs", prefs)
                
                # Try to find Chrome/Chromium binary
                try:
                    self.driver = webdriver.Chrome(options=options)
                except Exception:
                    # Fallback to explicit path or system Chrome
                    possible_paths = [
                        "/usr/bin/google-chrome",
                        "/usr/bin/chromium-browser",
                        "/usr/bin/chromium",
                        "/opt/google/chrome/chrome"
                    ]
                    for path in possible_paths:
                        if os.path.exists(path):
                            options.binary_location = path
                            self.driver = webdriver.Chrome(options=options)
                            break
                    else:
                        raise Exception("Chrome/Chromium not found")
                        
            elif browser == "firefox":
                options = FirefoxOptions()
                if headless:
                    options.add_argument("--headless")
                
                if user_data_dir:
                    profile = webdriver.FirefoxProfile(user_data_dir)
                    self.driver = webdriver.Firefox(firefox_profile=profile, options=options)
                else:
                    self.driver = webdriver.Firefox(options=options)
                    
                self.driver.set_window_size(width, height)
                
            else:
                return {"success": False, "error": f"Unsupported browser: {browser}"}
            
            # Set implicit wait
            self.driver.implicitly_wait(self.implicit_wait)
            
            # Generate session ID
            self.session_id = f"browser_session_{int(time.time())}"
            
            return {
                "success": True,
                "message": f"Browser {browser} started successfully",
                "session_id": self.session_id,
                "window_size": f"{width}x{height}",
                "headless": headless
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to start browser: {str(e)}"}
    
    def stop_browser(self) -> Dict:
        """Stop browser session"""
        if not self.driver:
            return {"success": False, "error": "No browser session active"}
        
        try:
            self.driver.quit()
            self.driver = None
            self.session_id = None
            self.page_history.clear()
            
            return {"success": True, "message": "Browser session stopped"}
            
        except Exception as e:
            return {"success": False, "error": f"Failed to stop browser: {str(e)}"}
    
    def navigate_to(self, url: str, wait_for_load: bool = True) -> Dict:
        """Navigate to URL"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            self.driver.get(url)
            
            if wait_for_load:
                # Wait for page to load
                WebDriverWait(self.driver, self.default_timeout).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            
            # Add to history
            self.page_history.append({
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "title": self.driver.title
            })
            
            return {
                "success": True,
                "url": self.driver.current_url,
                "title": self.driver.title,
                "message": f"Navigated to {url}"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Navigation failed: {str(e)}"}
    
    def go_back(self) -> Dict:
        """Navigate back in browser history"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            self.driver.back()
            return {
                "success": True,
                "url": self.driver.current_url,
                "title": self.driver.title,
                "message": "Navigated back"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Back navigation failed: {str(e)}"}
    
    def go_forward(self) -> Dict:
        """Navigate forward in browser history"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            self.driver.forward()
            return {
                "success": True,
                "url": self.driver.current_url,
                "title": self.driver.title,
                "message": "Navigated forward"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Forward navigation failed: {str(e)}"}
    
    def refresh_page(self) -> Dict:
        """Refresh current page"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            self.driver.refresh()
            return {
                "success": True,
                "url": self.driver.current_url,
                "title": self.driver.title,
                "message": "Page refreshed"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Page refresh failed: {str(e)}"}
    
    def find_element(self, selector: str, selector_type: str = "css", timeout: int = 10):
        """Find element by selector"""
        wait = WebDriverWait(self.driver, timeout)
        
        by_map = {
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "id": By.ID,
            "class": By.CLASS_NAME,
            "name": By.NAME,
            "tag": By.TAG_NAME,
            "link_text": By.LINK_TEXT,
            "partial_link_text": By.PARTIAL_LINK_TEXT
        }
        
        by = by_map.get(selector_type, By.CSS_SELECTOR)
        
        try:
            element = wait.until(EC.presence_of_element_located((by, selector)))
            return element
        except TimeoutException:
            raise Exception(f"Element not found: {selector} (type: {selector_type})")
    
    def click_element(self, selector: str, selector_type: str = "css", wait_timeout: int = 10,
                     double_click: bool = False) -> Dict:
        """Click on element"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            element = self.find_element(selector, selector_type, wait_timeout)
            
            # Scroll to element if needed
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            if double_click:
                ActionChains(self.driver).double_click(element).perform()
                action = "Double clicked"
            else:
                element.click()
                action = "Clicked"
            
            return {
                "success": True,
                "message": f"{action} element: {selector}",
                "element_text": element.text[:100] if element.text else ""
            }
            
        except Exception as e:
            return {"success": False, "error": f"Click failed: {str(e)}"}
    
    def type_text(self, selector: str, text: str, selector_type: str = "css", clear_first: bool = True,
                 press_enter: bool = False) -> Dict:
        """Type text into element"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            element = self.find_element(selector, selector_type)
            
            if clear_first:
                element.clear()
            
            element.send_keys(text)
            
            if press_enter:
                element.send_keys(Keys.RETURN)
            
            return {
                "success": True,
                "message": f"Typed text into element: {selector}",
                "text_length": len(text)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Type text failed: {str(e)}"}
    
    def get_element_text(self, selector: str, selector_type: str = "css", multiple: bool = False,
                        attribute: str = None) -> Dict:
        """Get text content from element(s)"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            if multiple:
                by_map = {
                    "css": By.CSS_SELECTOR,
                    "xpath": By.XPATH,
                    "id": By.ID,
                    "class": By.CLASS_NAME,
                    "name": By.NAME,
                    "tag": By.TAG_NAME
                }
                
                by = by_map.get(selector_type, By.CSS_SELECTOR)
                elements = self.driver.find_elements(by, selector)
                
                if attribute:
                    texts = [elem.get_attribute(attribute) for elem in elements]
                else:
                    texts = [elem.text for elem in elements]
                
                return {
                    "success": True,
                    "data": texts,
                    "count": len(texts),
                    "selector": selector
                }
            else:
                element = self.find_element(selector, selector_type)
                
                if attribute:
                    text = element.get_attribute(attribute)
                else:
                    text = element.text
                
                return {
                    "success": True,
                    "data": text,
                    "selector": selector
                }
                
        except Exception as e:
            return {"success": False, "error": f"Get text failed: {str(e)}"}
    
    def wait_for_element(self, selector: str, selector_type: str = "css", condition: str = "present",
                        timeout: int = 10) -> Dict:
        """Wait for element condition"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            by_map = {
                "css": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
                "class": By.CLASS_NAME,
                "name": By.NAME,
                "tag": By.TAG_NAME
            }
            
            by = by_map.get(selector_type, By.CSS_SELECTOR)
            wait = WebDriverWait(self.driver, timeout)
            
            if condition == "present":
                wait.until(EC.presence_of_element_located((by, selector)))
            elif condition == "visible":
                wait.until(EC.visibility_of_element_located((by, selector)))
            elif condition == "clickable":
                wait.until(EC.element_to_be_clickable((by, selector)))
            elif condition == "invisible":
                wait.until(EC.invisibility_of_element_located((by, selector)))
            
            return {
                "success": True,
                "message": f"Element condition '{condition}' met for: {selector}"
            }
            
        except TimeoutException:
            return {"success": False, "error": f"Timeout waiting for element condition: {condition}"}
        except Exception as e:
            return {"success": False, "error": f"Wait failed: {str(e)}"}
    
    def scroll_page(self, direction: str = "down", amount: int = 500, element_selector: str = None) -> Dict:
        """Scroll page or element"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            if element_selector:
                element = self.find_element(element_selector)
                target = element
            else:
                target = None
            
            if direction == "top":
                script = "arguments[0] ? arguments[0].scrollTop = 0 : window.scrollTo(0, 0);"
            elif direction == "bottom":
                script = "arguments[0] ? arguments[0].scrollTop = arguments[0].scrollHeight : window.scrollTo(0, document.body.scrollHeight);"
            elif direction == "up":
                script = f"arguments[0] ? arguments[0].scrollTop -= {amount} : window.scrollBy(0, -{amount});"
            elif direction == "down":
                script = f"arguments[0] ? arguments[0].scrollTop += {amount} : window.scrollBy(0, {amount});"
            elif direction == "left":
                script = f"arguments[0] ? arguments[0].scrollLeft -= {amount} : window.scrollBy(-{amount}, 0);"
            elif direction == "right":
                script = f"arguments[0] ? arguments[0].scrollLeft += {amount} : window.scrollBy({amount}, 0);"
            else:
                return {"success": False, "error": f"Invalid scroll direction: {direction}"}
            
            self.driver.execute_script(script, target)
            
            return {
                "success": True,
                "message": f"Scrolled {direction}" + (f" by {amount}px" if direction not in ["top", "bottom"] else "")
            }
            
        except Exception as e:
            return {"success": False, "error": f"Scroll failed: {str(e)}"}
    
    def take_screenshot(self, filename: str = None, element_selector: str = None, full_page: bool = False) -> Dict:
        """Take screenshot of page or element"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            screenshot_path = self.screenshots_dir / filename
            
            if element_selector:
                # Screenshot specific element
                element = self.find_element(element_selector)
                element_screenshot = element.screenshot_as_png
                with open(screenshot_path, 'wb') as f:
                    f.write(element_screenshot)
            elif full_page:
                # Full page screenshot (Chrome only)
                if self.browser_type == "chrome":
                    # Get page dimensions
                    total_height = self.driver.execute_script("return document.body.scrollHeight")
                    viewport_height = self.driver.execute_script("return window.innerHeight")
                    
                    # Take multiple screenshots and stitch them together
                    screenshots = []
                    scroll_position = 0
                    
                    while scroll_position < total_height:
                        self.driver.execute_script(f"window.scrollTo(0, {scroll_position})")
                        time.sleep(0.2)
                        screenshots.append(self.driver.get_screenshot_as_png())
                        scroll_position += viewport_height
                    
                    if IMAGE_PROCESSING_AVAILABLE:
                        # Stitch screenshots together
                        images = [Image.open(io.BytesIO(screenshot)) for screenshot in screenshots]
                        total_width = images[0].width
                        total_height = sum(img.height for img in images)
                        
                        combined = Image.new('RGB', (total_width, total_height))
                        y_offset = 0
                        for img in images:
                            combined.paste(img, (0, y_offset))
                            y_offset += img.height
                        
                        combined.save(screenshot_path)
                    else:
                        # Just save last screenshot
                        with open(screenshot_path, 'wb') as f:
                            f.write(screenshots[-1])
                else:
                    # Firefox doesn't support full page easily, just take regular screenshot
                    self.driver.save_screenshot(str(screenshot_path))
            else:
                # Regular viewport screenshot
                self.driver.save_screenshot(str(screenshot_path))
            
            return {
                "success": True,
                "screenshot_path": str(screenshot_path),
                "filename": filename,
                "url": self.driver.current_url,
                "title": self.driver.title
            }
            
        except Exception as e:
            return {"success": False, "error": f"Screenshot failed: {str(e)}"}
    
    def execute_javascript(self, script: str, arguments: List = None) -> Dict:
        """Execute JavaScript code"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            if arguments:
                result = self.driver.execute_script(script, *arguments)
            else:
                result = self.driver.execute_script(script)
            
            return {
                "success": True,
                "result": result,
                "script": script[:100] + "..." if len(script) > 100 else script
            }
            
        except Exception as e:
            return {"success": False, "error": f"JavaScript execution failed: {str(e)}"}
    
    def get_page_source(self, save_to_file: str = None) -> Dict:
        """Get current page HTML source"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            source = self.driver.page_source
            
            result = {
                "success": True,
                "url": self.driver.current_url,
                "title": self.driver.title,
                "source_length": len(source)
            }
            
            if save_to_file:
                with open(save_to_file, 'w', encoding='utf-8') as f:
                    f.write(source)
                result["saved_to"] = save_to_file
            else:
                # Return first 1000 characters as preview
                result["source_preview"] = source[:1000] + "..." if len(source) > 1000 else source
            
            return result
            
        except Exception as e:
            return {"success": False, "error": f"Get page source failed: {str(e)}"}
    
    def get_page_info(self) -> Dict:
        """Get current page information"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            info = {
                "url": self.driver.current_url,
                "title": self.driver.title,
                "page_source_length": len(self.driver.page_source),
                "window_size": self.driver.get_window_size(),
                "browser_type": self.browser_type,
                "session_id": self.session_id,
                "current_window_handle": self.driver.current_window_handle,
                "window_handles": self.driver.window_handles,
                "page_history": self.page_history[-5:],  # Last 5 pages
            }
            
            # Try to get additional page info via JavaScript
            try:
                js_info = self.driver.execute_script("""
                    return {
                        ready_state: document.readyState,
                        domain: document.domain,
                        referrer: document.referrer,
                        last_modified: document.lastModified,
                        cookie_enabled: navigator.cookieEnabled,
                        user_agent: navigator.userAgent,
                        viewport_width: window.innerWidth,
                        viewport_height: window.innerHeight,
                        scroll_position: {x: window.scrollX, y: window.scrollY},
                        page_dimensions: {
                            width: document.documentElement.scrollWidth,
                            height: document.documentElement.scrollHeight
                        }
                    };
                """)
                info.update(js_info)
            except Exception:
                pass  # JS info is optional
            
            return {"success": True, "data": info}
            
        except Exception as e:
            return {"success": False, "error": f"Get page info failed: {str(e)}"}
    
    def hover_element(self, selector: str, selector_type: str = "css") -> Dict:
        """Hover over element"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            element = self.find_element(selector, selector_type)
            ActionChains(self.driver).move_to_element(element).perform()
            
            return {
                "success": True,
                "message": f"Hovered over element: {selector}"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Hover failed: {str(e)}"}
    
    def drag_and_drop(self, source_selector: str, target_selector: str, selector_type: str = "css") -> Dict:
        """Drag and drop element"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            source = self.find_element(source_selector, selector_type)
            target = self.find_element(target_selector, selector_type)
            
            ActionChains(self.driver).drag_and_drop(source, target).perform()
            
            return {
                "success": True,
                "message": f"Dragged {source_selector} to {target_selector}"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Drag and drop failed: {str(e)}"}
    
    def get_cookies(self, domain: str = None) -> Dict:
        """Get browser cookies"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            cookies = self.driver.get_cookies()
            
            if domain:
                cookies = [cookie for cookie in cookies if domain in cookie.get('domain', '')]
            
            return {
                "success": True,
                "cookies": cookies,
                "count": len(cookies),
                "domain_filter": domain
            }
            
        except Exception as e:
            return {"success": False, "error": f"Get cookies failed: {str(e)}"}
    
    def set_cookie(self, name: str, value: str, domain: str = None, path: str = "/") -> Dict:
        """Set browser cookie"""
        if not self.check_browser_status():
            return {"success": False, "error": "No active browser session"}
        
        try:
            cookie_dict = {"name": name, "value": value, "path": path}
            
            if domain:
                cookie_dict["domain"] = domain
            
            self.driver.add_cookie(cookie_dict)
            
            return {
                "success": True,
                "message": f"Cookie set: {name}={value}",
                "cookie": cookie_dict
            }
            
        except Exception as e:
            return {"success": False, "error": f"Set cookie failed: {str(e)}"}
    
    def wait_and_pause(self, seconds: float = 1) -> Dict:
        """Wait/pause for specified time"""
        try:
            time.sleep(seconds)
            
            return {
                "success": True,
                "message": f"Paused for {seconds} seconds"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Pause failed: {str(e)}"}
    
    def handle_tool_call(self, tool_name: str, arguments: Dict) -> Dict:
        """Handle browser automation tool calls"""
        try:
            if tool_name == "browser_start":
                return self.start_browser(**arguments)
            elif tool_name == "browser_stop":
                return self.stop_browser()
            elif tool_name == "browser_navigate":
                return self.navigate_to(**arguments)
            elif tool_name == "browser_back":
                return self.go_back()
            elif tool_name == "browser_forward":
                return self.go_forward()
            elif tool_name == "browser_refresh":
                return self.refresh_page()
            elif tool_name == "browser_click":
                return self.click_element(**arguments)
            elif tool_name == "browser_type":
                return self.type_text(**arguments)
            elif tool_name == "browser_get_text":
                return self.get_element_text(**arguments)
            elif tool_name == "browser_wait_for_element":
                return self.wait_for_element(**arguments)
            elif tool_name == "browser_scroll":
                return self.scroll_page(**arguments)
            elif tool_name == "browser_screenshot":
                return self.take_screenshot(**arguments)
            elif tool_name == "browser_execute_js":
                return self.execute_javascript(**arguments)
            elif tool_name == "browser_get_page_source":
                return self.get_page_source(**arguments)
            elif tool_name == "browser_get_page_info":
                return self.get_page_info()
            elif tool_name == "browser_hover":
                return self.hover_element(**arguments)
            elif tool_name == "browser_drag_and_drop":
                return self.drag_and_drop(**arguments)
            elif tool_name == "browser_get_cookies":
                return self.get_cookies(**arguments)
            elif tool_name == "browser_set_cookie":
                return self.set_cookie(**arguments)
            elif tool_name == "browser_wait_and_pause":
                return self.wait_and_pause(**arguments)
            # Frame/tab switching tools need implementation
            elif tool_name in ["browser_switch_to_frame", "browser_switch_to_tab"]:
                return {"success": False, "error": f"Tool {tool_name} not implemented yet"}
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}

def main():
    """Main MCP server loop for Browser Automation"""
    server = BrowserMCPServer()
    
    print("🌐 Browser MCP Server Started", file=sys.stderr)
    print(f"🔧 Selenium: {'✅ Available' if SELENIUM_AVAILABLE else '❌ Missing (pip install selenium)'}", file=sys.stderr)
    print(f"📸 PIL: {'✅ Available' if IMAGE_PROCESSING_AVAILABLE else '❌ Missing (pip install pillow)'}", file=sys.stderr)
    print(f"📁 Screenshots: {server.screenshots_dir}", file=sys.stderr)
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            method = request.get("method", "")
            
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "Browser MCP Server",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {"tools": server.get_tools()}
                }
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                
                result = server.handle_tool_call(tool_name, arguments)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            elif method == "notifications/initialized":
                continue  # No response needed
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()