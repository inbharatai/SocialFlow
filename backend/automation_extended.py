"""
SocialFlow Extended - Additional Platform Automations
Facebook, Discord, Reddit, Medium, Substack, HeyGen, Email/Newsletter
Uses Playwright browser automation — login with email/password like a human
"""

import asyncio
import json
import os
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from automation import SocialAutomation, SESSIONS_DIR


class FacebookAutomation(SocialAutomation):
    """Facebook browser automation"""

    PLATFORM = "facebook"
    LOGIN_URL = "https://www.facebook.com/login"
    HOME_URL = "https://www.facebook.com/"

    async def login(self, email: str, password: str) -> dict:
        await self.init_browser()
        await self.create_new_context()

        try:
            await self.page.goto(self.LOGIN_URL)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)

            # Handle cookie consent
            try:
                cookie_btn = await self.page.query_selector(
                    'button[data-cookiebanner="accept_button"], '
                    'button:has-text("Allow"), button:has-text("Accept All")'
                )
                if cookie_btn:
                    await cookie_btn.click()
                    await self.page.wait_for_timeout(1000)
            except Exception:
                pass

            await self.page.fill('input#email, input[name="email"]', email)
            await self.page.fill('input#pass, input[name="pass"]', password)
            await self.page.click('button[name="login"], button[type="submit"]')

            await self.page.wait_for_timeout(5000)

            # Handle security checkpoint
            if "checkpoint" in self.page.url:
                print("Security verification required. Complete it in the browser...")
                await self.page.wait_for_url("**/facebook.com/**", timeout=120000)

            if "login" not in self.page.url:
                await self.save_session(self.PLATFORM)
                return {"success": True, "message": "Logged in to Facebook"}
            else:
                return {"success": False, "message": "Facebook login failed"}

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def check_login(self) -> bool:
        await self.init_browser()
        if await self.load_session(self.PLATFORM):
            try:
                await self.page.goto(self.HOME_URL)
                await self.page.wait_for_load_state("networkidle")
                return "login" not in self.page.url
            except Exception:
                pass
        return False

    async def post(self, content: str, image_paths: List[str] = None) -> dict:
        await self.init_browser()

        if not await self.load_session(self.PLATFORM):
            return {"success": False, "message": "Not logged in to Facebook"}

        try:
            await self.page.goto(self.HOME_URL)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)

            # Click "What's on your mind?" composer
            composer_trigger = await self.page.wait_for_selector(
                'div[role="button"]:has-text("What\'s on your mind"), '
                'span:has-text("What\'s on your mind")',
                timeout=10000
            )
            await composer_trigger.click()
            await self.page.wait_for_timeout(2000)

            # Find the text editor
            editor = await self.page.wait_for_selector(
                'div[contenteditable="true"][role="textbox"]',
                timeout=10000
            )
            await editor.click()
            await self.page.keyboard.type(content, delay=25)
            await self.page.wait_for_timeout(1000)

            # Handle images
            if image_paths:
                try:
                    photo_btn = await self.page.query_selector(
                        'div[aria-label*="Photo"], div[aria-label*="photo"]'
                    )
                    if photo_btn:
                        await photo_btn.click()
                        await self.page.wait_for_timeout(1000)

                    file_input = await self.page.wait_for_selector(
                        'input[type="file"][accept*="image"]', timeout=5000
                    )
                    await file_input.set_input_files(image_paths)
                    await self.page.wait_for_timeout(3000)
                except Exception:
                    pass

            # Click Post button
            post_btn = await self.page.wait_for_selector(
                'div[aria-label="Post"]:not([aria-disabled="true"]), '
                'span:has-text("Post")',
                timeout=10000
            )
            await post_btn.click()
            await self.page.wait_for_timeout(4000)

            await self.save_session(self.PLATFORM)
            return {"success": True, "message": "Posted to Facebook"}

        except Exception as e:
            return {"success": False, "message": f"Facebook post failed: {str(e)}"}
        finally:
            await self.close()


class RedditAutomation(SocialAutomation):
    """Reddit browser automation — manual-first, draft support"""

    PLATFORM = "reddit"
    LOGIN_URL = "https://www.reddit.com/login"
    HOME_URL = "https://www.reddit.com/"

    async def login(self, username: str, password: str) -> dict:
        await self.init_browser()
        await self.create_new_context()

        try:
            await self.page.goto(self.LOGIN_URL)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)

            username_input = await self.page.wait_for_selector(
                'input#loginUsername, input[name="username"]', timeout=10000
            )
            await username_input.fill(username)

            password_input = await self.page.wait_for_selector(
                'input#loginPassword, input[name="password"]'
            )
            await password_input.fill(password)

            login_btn = await self.page.wait_for_selector(
                'button[type="submit"]:has-text("Log In"), button:has-text("Log In")'
            )
            await login_btn.click()
            await self.page.wait_for_timeout(5000)

            if "login" not in self.page.url:
                await self.save_session(self.PLATFORM)
                return {"success": True, "message": "Logged in to Reddit"}
            else:
                return {"success": False, "message": "Reddit login failed"}

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def check_login(self) -> bool:
        await self.init_browser()
        if await self.load_session(self.PLATFORM):
            try:
                await self.page.goto(self.HOME_URL)
                await self.page.wait_for_load_state("networkidle")
                return "login" not in self.page.url
            except Exception:
                pass
        return False

    async def post(self, content: str, image_paths: List[str] = None,
                   subreddit: str = None, title: str = None) -> dict:
        """Post to a subreddit. Requires subreddit name and title."""
        if not subreddit:
            return {"success": False, "message": "Subreddit is required for Reddit posts"}
        if not title:
            return {"success": False, "message": "Title is required for Reddit posts"}

        await self.init_browser()

        if not await self.load_session(self.PLATFORM):
            return {"success": False, "message": "Not logged in to Reddit"}

        try:
            submit_url = f"https://www.reddit.com/r/{subreddit}/submit"
            await self.page.goto(submit_url)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(3000)

            # Fill title
            title_input = await self.page.wait_for_selector(
                'textarea[placeholder*="Title"], input[placeholder*="Title"], '
                'div[data-placeholder*="Title"]',
                timeout=10000
            )
            await title_input.fill(title)
            await self.page.wait_for_timeout(500)

            # Switch to text tab if needed and fill body
            try:
                text_tab = await self.page.query_selector(
                    'button:has-text("Text"), span:has-text("Text")'
                )
                if text_tab:
                    await text_tab.click()
                    await self.page.wait_for_timeout(500)
            except Exception:
                pass

            body_editor = await self.page.wait_for_selector(
                'div[contenteditable="true"], textarea[placeholder*="Text"]',
                timeout=5000
            )
            await body_editor.click()
            await self.page.keyboard.type(content, delay=20)
            await self.page.wait_for_timeout(1000)

            # Click Post
            post_btn = await self.page.wait_for_selector(
                'button:has-text("Post"), button[type="submit"]:has-text("Post")',
                timeout=10000
            )
            await post_btn.click()
            await self.page.wait_for_timeout(5000)

            await self.save_session(self.PLATFORM)
            return {"success": True, "message": f"Posted to r/{subreddit}"}

        except Exception as e:
            return {"success": False, "message": f"Reddit post failed: {str(e)}"}
        finally:
            await self.close()


class MediumAutomation(SocialAutomation):
    """Medium browser automation"""

    PLATFORM = "medium"
    LOGIN_URL = "https://medium.com/m/signin"
    HOME_URL = "https://medium.com/"
    NEW_STORY_URL = "https://medium.com/new-story"

    async def login(self, email: str, password: str) -> dict:
        await self.init_browser()
        await self.create_new_context()

        try:
            await self.page.goto(self.LOGIN_URL)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)

            # Medium uses Google/email sign-in flow
            # Click "Sign in with email"
            email_btn = await self.page.query_selector(
                'button:has-text("Sign in with email"), '
                'a:has-text("Sign in with email")'
            )
            if email_btn:
                await email_btn.click()
                await self.page.wait_for_timeout(2000)

            # Enter email
            email_input = await self.page.wait_for_selector(
                'input[type="email"], input[placeholder*="email"]',
                timeout=10000
            )
            await email_input.fill(email)

            # Look for continue/submit
            continue_btn = await self.page.query_selector(
                'button:has-text("Continue"), button[type="submit"]'
            )
            if continue_btn:
                await continue_btn.click()

            await self.page.wait_for_timeout(5000)

            # Medium may send magic link or show password field
            try:
                pw_input = await self.page.query_selector('input[type="password"]')
                if pw_input:
                    await pw_input.fill(password)
                    submit_btn = await self.page.query_selector(
                        'button[type="submit"], button:has-text("Sign in")'
                    )
                    if submit_btn:
                        await submit_btn.click()
                    await self.page.wait_for_timeout(5000)
            except Exception:
                pass

            if "signin" not in self.page.url and "login" not in self.page.url:
                await self.save_session(self.PLATFORM)
                return {"success": True, "message": "Logged in to Medium"}
            else:
                return {"success": False,
                        "message": "Medium login may require magic link. Check your email."}

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def check_login(self) -> bool:
        await self.init_browser()
        if await self.load_session(self.PLATFORM):
            try:
                await self.page.goto(self.HOME_URL)
                await self.page.wait_for_load_state("networkidle")
                # Check if we can access new-story page
                await self.page.goto(self.NEW_STORY_URL)
                await self.page.wait_for_timeout(2000)
                return "new-story" in self.page.url or "p/" in self.page.url
            except Exception:
                pass
        return False

    async def post(self, content: str, image_paths: List[str] = None,
                   title: str = None) -> dict:
        """Create a draft story on Medium"""
        await self.init_browser()

        if not await self.load_session(self.PLATFORM):
            return {"success": False, "message": "Not logged in to Medium"}

        try:
            await self.page.goto(self.NEW_STORY_URL)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(3000)

            # Title field
            title_field = await self.page.wait_for_selector(
                'h3[data-testid="editorTitle"], '
                'div[data-placeholder="Title"], '
                'h3[contenteditable="true"]',
                timeout=10000
            )
            await title_field.click()
            await self.page.keyboard.type(title or "Untitled", delay=20)
            await self.page.keyboard.press("Enter")
            await self.page.wait_for_timeout(500)

            # Body — type content line by line for proper formatting
            lines = content.split('\n')
            for line in lines:
                await self.page.keyboard.type(line, delay=10)
                await self.page.keyboard.press("Enter")

            await self.page.wait_for_timeout(2000)

            # Medium auto-saves drafts
            await self.save_session(self.PLATFORM)
            return {"success": True,
                    "message": "Draft created on Medium (auto-saved). Review and publish manually."}

        except Exception as e:
            return {"success": False, "message": f"Medium draft failed: {str(e)}"}
        finally:
            await self.close()


class SubstackAutomation(SocialAutomation):
    """Substack browser automation"""

    PLATFORM = "substack"
    LOGIN_URL = "https://substack.com/sign-in"

    def __init__(self, headless: bool = False, publication_url: str = None):
        super().__init__(headless)
        self.publication_url = publication_url or ""

    async def login(self, email: str, password: str) -> dict:
        await self.init_browser()
        await self.create_new_context()

        try:
            await self.page.goto(self.LOGIN_URL)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)

            # Enter email
            email_input = await self.page.wait_for_selector(
                'input[type="email"], input[name="email"], input[placeholder*="email"]',
                timeout=10000
            )
            await email_input.fill(email)

            # Click continue
            continue_btn = await self.page.query_selector(
                'button:has-text("Continue"), button:has-text("Sign in"), '
                'button[type="submit"]'
            )
            if continue_btn:
                await continue_btn.click()
            await self.page.wait_for_timeout(2000)

            # Password field
            try:
                pw_input = await self.page.wait_for_selector(
                    'input[type="password"]', timeout=5000
                )
                await pw_input.fill(password)
                submit_btn = await self.page.query_selector(
                    'button:has-text("Sign in"), button[type="submit"]'
                )
                if submit_btn:
                    await submit_btn.click()
                await self.page.wait_for_timeout(5000)
            except Exception:
                return {"success": False,
                        "message": "Substack may use magic link. Check your email."}

            if "sign-in" not in self.page.url:
                await self.save_session(self.PLATFORM)
                return {"success": True, "message": "Logged in to Substack"}
            else:
                return {"success": False, "message": "Substack login failed"}

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def check_login(self) -> bool:
        await self.init_browser()
        if await self.load_session(self.PLATFORM):
            try:
                await self.page.goto("https://substack.com/home")
                await self.page.wait_for_load_state("networkidle")
                return "sign-in" not in self.page.url
            except Exception:
                pass
        return False

    async def post(self, content: str, image_paths: List[str] = None,
                   title: str = None, subtitle: str = None) -> dict:
        """Create a draft post on Substack"""
        await self.init_browser()

        if not await self.load_session(self.PLATFORM):
            return {"success": False, "message": "Not logged in to Substack"}

        try:
            # Navigate to new post editor
            new_post_url = f"{self.publication_url}/publish/post" if self.publication_url else "https://substack.com/home"
            await self.page.goto(new_post_url)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(3000)

            # Title
            title_field = await self.page.wait_for_selector(
                'div[data-placeholder="Title"], '
                'textarea[placeholder*="Title"], '
                'div[role="textbox"]',
                timeout=10000
            )
            await title_field.click()
            await self.page.keyboard.type(title or "Newsletter Draft", delay=20)
            await self.page.keyboard.press("Tab")
            await self.page.wait_for_timeout(500)

            # Subtitle if available
            if subtitle:
                try:
                    subtitle_field = await self.page.query_selector(
                        'div[data-placeholder="Subtitle"], textarea[placeholder*="subtitle"]'
                    )
                    if subtitle_field:
                        await subtitle_field.click()
                        await self.page.keyboard.type(subtitle, delay=15)
                        await self.page.keyboard.press("Tab")
                except Exception:
                    pass

            # Body content
            await self.page.wait_for_timeout(500)
            lines = content.split('\n')
            for line in lines:
                await self.page.keyboard.type(line, delay=10)
                await self.page.keyboard.press("Enter")

            await self.page.wait_for_timeout(2000)

            # Substack auto-saves drafts
            await self.save_session(self.PLATFORM)
            return {"success": True,
                    "message": "Draft created on Substack (auto-saved). Review and send from dashboard."}

        except Exception as e:
            return {"success": False, "message": f"Substack draft failed: {str(e)}"}
        finally:
            await self.close()


class DiscordAutomation:
    """Discord posting via webhook — no browser needed"""

    PLATFORM = "discord"

    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url

    async def post(self, content: str, image_paths: List[str] = None,
                   username: str = "OpenClaw CMO") -> dict:
        if not self.webhook_url:
            return {"success": False, "message": "Discord webhook URL not configured"}

        try:
            payload = {
                "username": username,
                "content": content[:2000]  # Discord limit
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=15.0
                )

            if response.status_code in (200, 204):
                return {"success": True, "message": "Posted to Discord"}
            else:
                return {"success": False,
                        "message": f"Discord webhook failed: HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def login(self, *args, **kwargs) -> dict:
        return {"success": True, "message": "Discord uses webhook — no login needed"}

    async def check_login(self) -> bool:
        return bool(self.webhook_url)

    async def close(self):
        pass


class HeyGenAutomation(SocialAutomation):
    """HeyGen browser automation for video creation"""

    PLATFORM = "heygen"
    LOGIN_URL = "https://app.heygen.com/login"
    HOME_URL = "https://app.heygen.com/home"

    async def login(self, email: str, password: str) -> dict:
        await self.init_browser()
        await self.create_new_context()

        try:
            await self.page.goto(self.LOGIN_URL)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(3000)

            # Fill email
            email_input = await self.page.wait_for_selector(
                'input[type="email"], input[name="email"], input[placeholder*="email"]',
                timeout=10000
            )
            await email_input.fill(email)

            # Fill password
            pw_input = await self.page.wait_for_selector(
                'input[type="password"], input[name="password"]'
            )
            await pw_input.fill(password)

            # Click sign in
            login_btn = await self.page.wait_for_selector(
                'button:has-text("Sign in"), button:has-text("Log in"), '
                'button[type="submit"]'
            )
            await login_btn.click()
            await self.page.wait_for_timeout(5000)

            if "login" not in self.page.url:
                await self.save_session(self.PLATFORM)
                return {"success": True, "message": "Logged in to HeyGen"}
            else:
                return {"success": False, "message": "HeyGen login failed"}

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def check_login(self) -> bool:
        await self.init_browser()
        if await self.load_session(self.PLATFORM):
            try:
                await self.page.goto(self.HOME_URL)
                await self.page.wait_for_load_state("networkidle")
                return "login" not in self.page.url
            except Exception:
                pass
        return False

    async def post(self, content: str, image_paths: List[str] = None) -> dict:
        """Navigate to HeyGen and prepare a video project from a script brief"""
        await self.init_browser()

        if not await self.load_session(self.PLATFORM):
            return {"success": False, "message": "Not logged in to HeyGen"}

        try:
            # Go to create new video
            await self.page.goto("https://app.heygen.com/create-v3/new")
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(5000)

            # HeyGen's editor requires visual interaction
            # We can navigate to the editor but script input varies by UI version
            # Best approach: open the editor and let the brief guide manual work

            await self.save_session(self.PLATFORM)
            return {"success": True,
                    "message": "HeyGen editor opened. Script brief is ready for manual video creation.",
                    "brief": content[:2000]}

        except Exception as e:
            return {"success": False, "message": f"HeyGen failed: {str(e)}"}
        finally:
            await self.close()


class EmailAutomation(SocialAutomation):
    """Generic email/newsletter platform browser automation
    Supports: beehiiv, MailerLite, Brevo via browser login
    """

    PLATFORMS = {
        "beehiiv": {
            "login_url": "https://app.beehiiv.com/login",
            "home_url": "https://app.beehiiv.com/",
            "new_post_url": "https://app.beehiiv.com/posts/new",
        },
        "mailerlite": {
            "login_url": "https://app.mailerlite.com/login",
            "home_url": "https://app.mailerlite.com/",
        },
        "brevo": {
            "login_url": "https://app.brevo.com/login",
            "home_url": "https://app.brevo.com/",
        },
    }

    def __init__(self, headless: bool = False, email_platform: str = "beehiiv"):
        super().__init__(headless)
        self.email_platform = email_platform.lower()
        config = self.PLATFORMS.get(self.email_platform, {})
        self.login_url = config.get("login_url", "")
        self.home_url = config.get("home_url", "")
        self.PLATFORM = f"email_{self.email_platform}"

    async def login(self, email: str, password: str) -> dict:
        if not self.login_url:
            return {"success": False, "message": f"Unknown email platform: {self.email_platform}"}

        await self.init_browser()
        await self.create_new_context()

        try:
            await self.page.goto(self.login_url)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)

            # Generic email/password login
            email_input = await self.page.wait_for_selector(
                'input[type="email"], input[name="email"], '
                'input[placeholder*="email"], input[placeholder*="Email"]',
                timeout=10000
            )
            await email_input.fill(email)

            pw_input = await self.page.wait_for_selector(
                'input[type="password"], input[name="password"]'
            )
            await pw_input.fill(password)

            submit_btn = await self.page.wait_for_selector(
                'button[type="submit"], button:has-text("Log in"), '
                'button:has-text("Sign in")'
            )
            await submit_btn.click()
            await self.page.wait_for_timeout(5000)

            if "login" not in self.page.url and "sign" not in self.page.url:
                await self.save_session(self.PLATFORM)
                return {"success": True, "message": f"Logged in to {self.email_platform}"}
            else:
                return {"success": False, "message": f"{self.email_platform} login failed"}

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def check_login(self) -> bool:
        await self.init_browser()
        if await self.load_session(self.PLATFORM):
            try:
                await self.page.goto(self.home_url)
                await self.page.wait_for_load_state("networkidle")
                return "login" not in self.page.url
            except Exception:
                pass
        return False

    async def post(self, content: str, image_paths: List[str] = None,
                   subject: str = None) -> dict:
        """Create a newsletter draft on the email platform"""
        await self.init_browser()

        if not await self.load_session(self.PLATFORM):
            return {"success": False, "message": f"Not logged in to {self.email_platform}"}

        try:
            # Navigate to compose/new post area
            if self.email_platform == "beehiiv":
                await self.page.goto("https://app.beehiiv.com/posts/new")
            else:
                await self.page.goto(self.home_url)

            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(3000)

            await self.save_session(self.PLATFORM)
            return {"success": True,
                    "message": f"Opened {self.email_platform} editor. Draft content ready for review.",
                    "subject": subject,
                    "content_preview": content[:500]}

        except Exception as e:
            return {"success": False, "message": f"{self.email_platform} failed: {str(e)}"}
        finally:
            await self.close()


# Extended factory function
def get_automation_extended(platform: str, headless: bool = False, **kwargs):
    """Get automation instance for any supported platform"""
    from automation import LinkedInAutomation, InstagramAutomation, TwitterAutomation

    platforms = {
        "linkedin": lambda: LinkedInAutomation(headless),
        "instagram": lambda: InstagramAutomation(headless),
        "twitter": lambda: TwitterAutomation(headless),
        "x": lambda: TwitterAutomation(headless),
        "facebook": lambda: FacebookAutomation(headless),
        "reddit": lambda: RedditAutomation(headless),
        "medium": lambda: MediumAutomation(headless),
        "substack": lambda: SubstackAutomation(headless, kwargs.get("publication_url")),
        "discord": lambda: DiscordAutomation(kwargs.get("webhook_url")),
        "heygen": lambda: _get_heygen(headless),
        "beehiiv": lambda: EmailAutomation(headless, "beehiiv"),
        "mailerlite": lambda: EmailAutomation(headless, "mailerlite"),
        "brevo": lambda: EmailAutomation(headless, "brevo"),
    }

    factory = platforms.get(platform.lower())
    if not factory:
        raise ValueError(f"Unsupported platform: {platform}. "
                        f"Supported: {', '.join(platforms.keys())}")
    return factory()


def _get_heygen(headless: bool):
    """Import and return the enhanced HeyGen adapter"""
    try:
        from heygen_adapter import HeyGenVideoAdapter
        return HeyGenVideoAdapter(headless)
    except ImportError:
        return HeyGenAutomation(headless)
