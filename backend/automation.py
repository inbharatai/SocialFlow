"""
SocialFlow - Browser Automation Module
Handles login and posting for LinkedIn, Instagram, and X (Twitter)
Uses Playwright for reliable browser automation
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Session storage directory
SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

class SocialAutomation:
    """Base class for social media automation"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
    
    async def init_browser(self):
        """Initialize the browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
    
    async def close(self):
        """Close browser and cleanup"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    def get_session_path(self, platform: str) -> Path:
        """Get path to session file for a platform"""
        return SESSIONS_DIR / f"{platform}_session.json"
    
    async def save_session(self, platform: str):
        """Save browser cookies/session"""
        if self.context:
            cookies = await self.context.cookies()
            storage = await self.context.storage_state()
            session_data = {
                "cookies": cookies,
                "storage": storage,
                "saved_at": datetime.now().isoformat()
            }
            with open(self.get_session_path(platform), 'w') as f:
                json.dump(session_data, f)
    
    async def load_session(self, platform: str) -> bool:
        """Load saved session if exists"""
        session_path = self.get_session_path(platform)
        if session_path.exists():
            try:
                with open(session_path, 'r') as f:
                    session_data = json.load(f)
                self.context = await self.browser.new_context(
                    storage_state=session_data["storage"],
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                self.page = await self.context.new_page()
                return True
            except Exception as e:
                print(f"Failed to load session: {e}")
        return False
    
    async def create_new_context(self):
        """Create a fresh browser context"""
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()


class LinkedInAutomation(SocialAutomation):
    """LinkedIn browser automation"""
    
    PLATFORM = "linkedin"
    LOGIN_URL = "https://www.linkedin.com/login"
    FEED_URL = "https://www.linkedin.com/feed/"
    
    async def login(self, email: str, password: str) -> dict:
        """Login to LinkedIn"""
        await self.init_browser()
        await self.create_new_context()
        
        try:
            await self.page.goto(self.LOGIN_URL)
            await self.page.wait_for_load_state("networkidle")
            
            # Fill credentials
            await self.page.fill('input#username', email)
            await self.page.fill('input#password', password)
            await self.page.click('button[type="submit"]')
            
            # Wait for navigation or security challenge
            await self.page.wait_for_timeout(3000)
            
            # Check for security verification
            if "checkpoint" in self.page.url or "challenge" in self.page.url:
                # Wait for user to complete verification manually
                print("⚠️ Security verification required. Please complete it in the browser...")
                await self.page.wait_for_url("**/feed/**", timeout=120000)
            
            # Verify login success
            if "/feed" in self.page.url:
                await self.save_session(self.PLATFORM)
                return {"success": True, "message": "Logged in successfully"}
            else:
                return {"success": False, "message": "Login failed - check credentials"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def check_login(self) -> bool:
        """Check if already logged in"""
        await self.init_browser()
        
        if await self.load_session(self.PLATFORM):
            try:
                await self.page.goto(self.FEED_URL)
                await self.page.wait_for_load_state("networkidle")
                return "/feed" in self.page.url
            except Exception:
                pass
        return False
    
    async def post(self, content: str, image_paths: List[str] = None) -> dict:
        """Create a post on LinkedIn"""
        await self.init_browser()
        
        if not await self.load_session(self.PLATFORM):
            return {"success": False, "message": "Not logged in"}
        
        try:
            await self.page.goto(self.FEED_URL)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)
            
            # Click "Start a post" button
            start_post_btn = await self.page.wait_for_selector(
                'button:has-text("Start a post"), button.share-box-feed-entry__trigger',
                timeout=10000
            )
            await start_post_btn.click()
            await self.page.wait_for_timeout(1500)
            
            # Find the post editor
            editor = await self.page.wait_for_selector(
                'div.ql-editor[contenteditable="true"], div[role="textbox"]',
                timeout=10000
            )
            
            # Type content
            await editor.click()
            await self.page.keyboard.type(content, delay=20)
            await self.page.wait_for_timeout(1000)
            
            # Handle images if provided
            if image_paths:
                # Click media button
                media_btn = await self.page.query_selector('button[aria-label*="Add media"], button:has-text("Media")')
                if media_btn:
                    await media_btn.click()
                    await self.page.wait_for_timeout(500)
                    
                    # Upload images
                    file_input = await self.page.wait_for_selector('input[type="file"]')
                    await file_input.set_input_files(image_paths)
                    await self.page.wait_for_timeout(2000)
            
            # Click Post button
            post_btn = await self.page.wait_for_selector(
                'button:has-text("Post"):not([disabled]), button.share-actions__primary-action',
                timeout=10000
            )
            await post_btn.click()
            
            # Wait for post to complete
            await self.page.wait_for_timeout(3000)
            
            await self.save_session(self.PLATFORM)
            return {"success": True, "message": "Posted successfully to LinkedIn"}
            
        except Exception as e:
            return {"success": False, "message": f"Failed to post: {str(e)}"}
        finally:
            await self.close()


class InstagramAutomation(SocialAutomation):
    """Instagram browser automation"""
    
    PLATFORM = "instagram"
    LOGIN_URL = "https://www.instagram.com/accounts/login/"
    HOME_URL = "https://www.instagram.com/"
    
    async def login(self, username: str, password: str) -> dict:
        """Login to Instagram"""
        await self.init_browser()
        await self.create_new_context()
        
        try:
            await self.page.goto(self.LOGIN_URL)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)
            
            # Handle cookie popup
            try:
                cookie_btn = await self.page.query_selector('button:has-text("Allow"), button:has-text("Accept")')
                if cookie_btn:
                    await cookie_btn.click()
                    await self.page.wait_for_timeout(1000)
            except Exception:
                pass
            
            # Fill credentials
            await self.page.fill('input[name="username"]', username)
            await self.page.fill('input[name="password"]', password)
            await self.page.click('button[type="submit"]')
            
            await self.page.wait_for_timeout(5000)
            
            # Handle "Save Login Info" popup
            try:
                save_btn = await self.page.query_selector('button:has-text("Save Info"), button:has-text("Not Now")')
                if save_btn:
                    await save_btn.click()
            except Exception:
                pass
            
            # Handle notifications popup
            try:
                notif_btn = await self.page.query_selector('button:has-text("Not Now")')
                if notif_btn:
                    await notif_btn.click()
            except Exception:
                pass
            
            await self.page.wait_for_timeout(2000)
            
            # Verify login
            if "login" not in self.page.url:
                await self.save_session(self.PLATFORM)
                return {"success": True, "message": "Logged in successfully"}
            else:
                return {"success": False, "message": "Login failed"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def check_login(self) -> bool:
        """Check if already logged in"""
        await self.init_browser()
        
        if await self.load_session(self.PLATFORM):
            try:
                await self.page.goto(self.HOME_URL)
                await self.page.wait_for_load_state("networkidle")
                return "login" not in self.page.url
            except Exception:
                pass
        return False
    
    async def post(self, content: str, image_paths: List[str]) -> dict:
        """Create a post on Instagram (requires at least one image)"""
        if not image_paths:
            return {"success": False, "message": "Instagram requires at least one image"}
        
        await self.init_browser()
        
        if not await self.load_session(self.PLATFORM):
            return {"success": False, "message": "Not logged in"}
        
        try:
            await self.page.goto(self.HOME_URL)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)
            
            # Click create post button (+ icon)
            create_btn = await self.page.wait_for_selector(
                'svg[aria-label="New post"], a[href="/create/select/"], span:has-text("Create")',
                timeout=10000
            )
            await create_btn.click()
            await self.page.wait_for_timeout(1500)
            
            # Upload image
            file_input = await self.page.wait_for_selector('input[type="file"]', timeout=10000)
            await file_input.set_input_files(image_paths)
            await self.page.wait_for_timeout(3000)
            
            # Click through the editing steps
            # Next button (crop screen)
            next_btn = await self.page.wait_for_selector('button:has-text("Next"), div[role="button"]:has-text("Next")')
            await next_btn.click()
            await self.page.wait_for_timeout(1500)
            
            # Next button (filters screen)
            next_btn = await self.page.wait_for_selector('button:has-text("Next"), div[role="button"]:has-text("Next")')
            await next_btn.click()
            await self.page.wait_for_timeout(1500)
            
            # Add caption
            caption_input = await self.page.wait_for_selector('textarea[aria-label*="caption"], textarea[placeholder*="caption"]')
            await caption_input.fill(content)
            await self.page.wait_for_timeout(1000)
            
            # Share button
            share_btn = await self.page.wait_for_selector('button:has-text("Share"), div[role="button"]:has-text("Share")')
            await share_btn.click()
            
            # Wait for post to complete
            await self.page.wait_for_timeout(5000)
            
            await self.save_session(self.PLATFORM)
            return {"success": True, "message": "Posted successfully to Instagram"}
            
        except Exception as e:
            return {"success": False, "message": f"Failed to post: {str(e)}"}
        finally:
            await self.close()


class TwitterAutomation(SocialAutomation):
    """X (Twitter) browser automation"""
    
    PLATFORM = "twitter"
    LOGIN_URL = "https://twitter.com/i/flow/login"
    HOME_URL = "https://twitter.com/home"
    
    async def login(self, username: str, password: str) -> dict:
        """Login to X (Twitter)"""
        await self.init_browser()
        await self.create_new_context()
        
        try:
            await self.page.goto(self.LOGIN_URL)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(3000)
            
            # Enter username/email
            username_input = await self.page.wait_for_selector(
                'input[autocomplete="username"], input[name="text"]',
                timeout=15000
            )
            await username_input.fill(username)
            
            # Click Next
            next_btn = await self.page.wait_for_selector('button:has-text("Next"), div[role="button"]:has-text("Next")')
            await next_btn.click()
            await self.page.wait_for_timeout(2000)
            
            # Check for "unusual activity" - may ask for phone/username verification
            try:
                unusual_input = await self.page.query_selector('input[data-testid="ocfEnterTextTextInput"]')
                if unusual_input:
                    print("⚠️ Twitter requires additional verification. Please complete it in the browser...")
                    # Wait for user to complete
                    await self.page.wait_for_timeout(30000)
            except Exception:
                pass
            
            # Enter password
            password_input = await self.page.wait_for_selector(
                'input[name="password"], input[type="password"]',
                timeout=10000
            )
            await password_input.fill(password)
            
            # Click Login
            login_btn = await self.page.wait_for_selector(
                'button[data-testid="LoginForm_Login_Button"], button:has-text("Log in")'
            )
            await login_btn.click()
            
            await self.page.wait_for_timeout(5000)
            
            # Verify login
            if "/home" in self.page.url or "twitter.com" in self.page.url and "login" not in self.page.url:
                await self.save_session(self.PLATFORM)
                return {"success": True, "message": "Logged in successfully"}
            else:
                return {"success": False, "message": "Login failed - check credentials"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def check_login(self) -> bool:
        """Check if already logged in"""
        await self.init_browser()
        
        if await self.load_session(self.PLATFORM):
            try:
                await self.page.goto(self.HOME_URL)
                await self.page.wait_for_load_state("networkidle")
                return "login" not in self.page.url and "/home" in self.page.url
            except Exception:
                pass
        return False
    
    async def post(self, content: str, image_paths: List[str] = None) -> dict:
        """Create a post (tweet) on X"""
        await self.init_browser()
        
        if not await self.load_session(self.PLATFORM):
            return {"success": False, "message": "Not logged in"}
        
        try:
            await self.page.goto(self.HOME_URL)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)
            
            # Find tweet composer
            composer = await self.page.wait_for_selector(
                'div[data-testid="tweetTextarea_0"], div[role="textbox"]',
                timeout=10000
            )
            await composer.click()
            await self.page.wait_for_timeout(500)
            
            # Type content
            await self.page.keyboard.type(content, delay=30)
            await self.page.wait_for_timeout(1000)
            
            # Handle images if provided
            if image_paths:
                file_input = await self.page.query_selector('input[data-testid="fileInput"], input[type="file"]')
                if file_input:
                    await file_input.set_input_files(image_paths)
                    await self.page.wait_for_timeout(2000)
            
            # Click Post button
            post_btn = await self.page.wait_for_selector(
                'button[data-testid="tweetButtonInline"], button:has-text("Post")',
                timeout=10000
            )
            await post_btn.click()
            
            await self.page.wait_for_timeout(3000)
            
            await self.save_session(self.PLATFORM)
            return {"success": True, "message": "Posted successfully to X"}
            
        except Exception as e:
            return {"success": False, "message": f"Failed to post: {str(e)}"}
        finally:
            await self.close()


# Factory function to get the right automation class
def get_automation(platform: str, headless: bool = False) -> SocialAutomation:
    """Get automation instance for a platform"""
    platforms = {
        "linkedin": LinkedInAutomation,
        "instagram": InstagramAutomation,
        "twitter": TwitterAutomation,
        "x": TwitterAutomation
    }
    
    automation_class = platforms.get(platform.lower())
    if not automation_class:
        raise ValueError(f"Unsupported platform: {platform}")
    
    return automation_class(headless=headless)


# Test functions
async def test_login(platform: str, username: str, password: str):
    """Test login for a platform"""
    auto = get_automation(platform)
    result = await auto.login(username, password)
    await auto.close()
    return result


async def test_post(platform: str, content: str, images: List[str] = None):
    """Test posting to a platform"""
    auto = get_automation(platform)
    result = await auto.post(content, images)
    await auto.close()
    return result
