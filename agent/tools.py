"""
Playwright Browser Tools for the IT Support Agent
--------------------------------------------------
All browser interactions are abstracted into high-level, human-like
tool functions. The agent calls these instead of raw Playwright API.

Design principle: Every tool logs what it's doing, so the agent can
observe the result before deciding the next action.
"""

import asyncio
import logging
import re
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger("agent.tools")


class BrowserTools:
    """
    Encapsulates all Playwright interactions as high-level agent tools.
    Acts like a human user navigating a browser.
    """

    def __init__(self, headless: bool = False):
        """
        Args:
            headless: If False, opens a visible browser window so you can
                      watch the agent work. Set True for background runs.
        """
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    # ----------------------------------------------------------------
    # Lifecycle management
    # ----------------------------------------------------------------

    async def start(self):
        """Launch the browser and create a fresh context."""
        logger.info("🚀 Launching browser...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=300,  # Slow down by 300ms — makes it feel human
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        )
        self._page = await self._context.new_page()
        logger.info("✅ Browser launched successfully.")

    async def close(self):
        """Cleanly shut down the browser."""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("🛑 Browser closed.")

    # ----------------------------------------------------------------
    # Core agent tools (the LLM will select from these)
    # ----------------------------------------------------------------

    async def open_url(self, url: str) -> dict:
        """
        Tool: open_url
        Navigate to a URL and wait for the page to fully load.
        Returns page title and current URL for observation.
        """
        logger.info(f"🌐 Navigating to: {url}")
        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
            # Extra wait to ensure JS rendering settles
            await asyncio.sleep(0.5)
            title = await self._page.title()
            current_url = self._page.url
            logger.info(f"   ✅ Loaded: '{title}' @ {current_url}")
            return {
                "success": True,
                "title": title,
                "url": current_url,
                "observation": f"Page loaded: '{title}' at {current_url}",
            }
        except Exception as e:
            logger.error(f"   ❌ Navigation failed: {e}")
            return {"success": False, "error": str(e), "observation": f"Failed to navigate: {e}"}

    async def click(self, selector: str, description: str = "") -> dict:
        """
        Tool: click
        Click an element by CSS selector or text content.
        Tries multiple strategies before giving up (robust to UI changes).

        Args:
            selector: CSS selector, text content, or element ID
            description: Human-readable description for logging
        """
        desc = description or selector
        logger.info(f"🖱️  Clicking: {desc}")

        strategies = [
            # Exact selector
            lambda: self._page.click(selector, timeout=5000),
            # By text
            lambda: self._page.click(f"text={selector}", timeout=5000),
            # By ID
            lambda: self._page.click(f"#{selector}", timeout=5000),
            # By placeholder
            lambda: self._page.click(f"[placeholder='{selector}']", timeout=5000),
        ]

        for i, strategy in enumerate(strategies):
            try:
                await strategy()
                logger.info(f"   ✅ Clicked successfully (strategy {i+1})")
                await asyncio.sleep(0.3)  # Brief pause after click
                return {"success": True, "observation": f"Clicked '{desc}' successfully."}
            except Exception:
                continue

        error_msg = f"Could not click '{desc}' — element not found or not clickable."
        logger.error(f"   ❌ {error_msg}")
        return {"success": False, "error": error_msg, "observation": error_msg}

    async def type_text(self, selector: str, text: str, description: str = "") -> dict:
        """
        Tool: type_text
        Clear a field and type text into it.
        Tries multiple selector strategies: exact, #id, [name=], [placeholder=].

        Args:
            selector: CSS selector or field ID
            text: Text to type
            description: Human-readable description for logging
        """
        desc = description or f"'{selector}' field"
        logger.info(f"⌨️  Typing into {desc}: '{text}'")

        selectors_to_try = [
            selector,                        # exact (e.g. already "#username" or "input")
            f"#{selector}",                  # as ID
            f"[name='{selector}']",          # by name attr
            f"[placeholder*='{selector}']",  # by placeholder (partial)
            f"input[id='{selector}']",       # explicit input by id
        ]

        for i, sel in enumerate(selectors_to_try):
            try:
                await self._page.fill(sel, text, timeout=4000)
                logger.info(f"   ✅ Typed successfully (strategy {i+1}: '{sel}')")
                return {"success": True, "observation": f"Typed '{text}' into {desc}."}
            except Exception:
                continue

        error_msg = f"Could not type into '{desc}' — field not found."
        logger.error(f"   ❌ {error_msg}")
        return {"success": False, "error": error_msg, "observation": error_msg}

    async def select_option(self, selector: str, value: str, description: str = "") -> dict:
        """
        Tool: select_option
        Select an option from a <select> dropdown by value.
        """
        desc = description or f"'{selector}' dropdown"
        logger.info(f"📋 Selecting '{value}' from {desc}")

        strategies = [
            lambda: self._page.select_option(selector, value=value, timeout=5000),
            lambda: self._page.select_option(f"#{selector}", value=value, timeout=5000),
            lambda: self._page.select_option(f"[name='{selector}']", value=value, timeout=5000),
        ]

        for i, strategy in enumerate(strategies):
            try:
                await strategy()
                logger.info(f"   ✅ Selected '{value}' (strategy {i+1})")
                return {"success": True, "observation": f"Selected '{value}' from {desc}."}
            except Exception:
                continue

        error_msg = f"Could not select '{value}' from '{desc}'."
        logger.error(f"   ❌ {error_msg}")
        return {"success": False, "error": error_msg, "observation": error_msg}

    async def extract_text(self, selector: str = "body") -> dict:
        """
        Tool: extract_text
        Extract visible text from the page or a specific element.
        Used for observation after page loads/actions.
        """
        logger.info(f"👁️  Extracting text from: {selector}")
        try:
            if selector == "body":
                text = await self._page.inner_text("body")
            else:
                text = await self._page.inner_text(selector)

            # Truncate for readability in logs
            short_text = text[:500].strip()
            logger.info(f"   📄 Extracted ({len(text)} chars): {short_text[:100]}...")
            return {
                "success": True,
                "text": text,
                "preview": short_text,
                "observation": f"Page content extracted ({len(text)} chars).",
            }
        except Exception as e:
            logger.error(f"   ❌ Extraction failed: {e}")
            return {"success": False, "error": str(e), "observation": f"Text extraction failed: {e}"}

    async def check_element_exists(self, selector: str) -> dict:
        """
        Tool: check_element_exists
        Check if a specific element (like a success message) is present.
        Used for conditional logic: IF user exists → skip creation.
        """
        logger.info(f"🔍 Checking if element exists: {selector}")
        try:
            element = await self._page.query_selector(selector)
            exists = element is not None
            logger.info(f"   {'✅ Found' if exists else '❌ Not found'}: {selector}")
            return {
                "success": True,
                "exists": exists,
                "observation": f"Element '{selector}' {'exists' if exists else 'does not exist'} on page.",
            }
        except Exception as e:
            return {"success": False, "exists": False, "observation": str(e)}

    async def get_page_text_contains(self, search_text: str) -> dict:
        """
        Tool: get_page_text_contains
        Check if the page body contains a specific string.
        Used for verification: "did the success message appear?"
        """
        logger.info(f"🔍 Checking if page contains: '{search_text}'")
        try:
            body_text = await self._page.inner_text("body")
            contains = search_text.lower() in body_text.lower()
            logger.info(f"   {'✅ Found' if contains else '❌ Not found'}: '{search_text}'")
            return {
                "success": True,
                "contains": contains,
                "observation": f"Page {'contains' if contains else 'does not contain'} '{search_text}'.",
            }
        except Exception as e:
            return {"success": False, "contains": False, "observation": str(e)}

    async def wait(self, seconds: float = 1.0) -> dict:
        """
        Tool: wait
        Pause execution for a given number of seconds.
        Used after navigation or before reading page content.
        """
        logger.info(f"⏳ Waiting {seconds}s...")
        await asyncio.sleep(seconds)
        return {"success": True, "observation": f"Waited {seconds} seconds."}

    async def take_screenshot(self, path: str = "screenshot.png") -> dict:
        """
        Tool: take_screenshot
        Capture the current page state for debugging.
        """
        logger.info(f"📸 Taking screenshot: {path}")
        try:
            await self._page.screenshot(path=path, full_page=True)
            return {"success": True, "path": path, "observation": f"Screenshot saved to {path}."}
        except Exception as e:
            return {"success": False, "error": str(e), "observation": f"Screenshot failed: {e}"}

    async def get_current_url(self) -> str:
        """Return the current page URL."""
        return self._page.url if self._page else ""

    async def submit_form(self, selector: str = "form") -> dict:
        """
        Tool: submit_form
        Submit a form by pressing Enter or clicking the submit button.
        """
        logger.info(f"📨 Submitting form: {selector}")
        try:
            # Try to find and click a submit button
            submit_btn = await self._page.query_selector(f"{selector} [type='submit']")
            if submit_btn:
                await submit_btn.click()
            else:
                await self._page.keyboard.press("Enter")

            await self._page.wait_for_load_state("networkidle", timeout=10000)
            logger.info("   ✅ Form submitted.")
            return {"success": True, "observation": "Form submitted and page reloaded."}
        except Exception as e:
            logger.error(f"   ❌ Form submission failed: {e}")
            return {"success": False, "error": str(e), "observation": f"Form submission failed: {e}"}
