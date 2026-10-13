"""Browser session management."""

import asyncio
from pathlib import Path
from typing import Optional
from playwright.async_api import Browser, BrowserContext, Page


class BrowserSession:
    """Manages a single browser session with isolated context."""

    def __init__(
        self,
        browser: Browser,
        session_id: str,
        headless: bool = True,
        profile_dir: Optional[Path] = None,
    ):
        self.browser = browser
        self.session_id = session_id
        self.headless = headless
        self.profile_dir = profile_dir
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._screenshot_counter = 0

    async def start(self) -> Page:
        """Initialize browser context and create first page."""
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

        if self.profile_dir:
            self.profile_dir.mkdir(parents=True, exist_ok=True)

        self.context = await self.browser.new_context(**context_options)

        # Enable tracing for debugging
        await self.context.tracing.start(screenshots=True, snapshots=True)

        self.page = await self.context.new_page()
        return self.page

    async def navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        """Navigate to URL."""
        if not self.page:
            raise RuntimeError("Session not started")
        await self.page.goto(url, wait_until=wait_until, timeout=30000)

    async def screenshot(self, path: Optional[Path] = None) -> bytes:
        """Take screenshot of current page."""
        if not self.page:
            raise RuntimeError("Session not started")

        if path:
            await self.page.screenshot(path=str(path), full_page=True)
            with open(path, "rb") as f:
                return f.read()
        else:
            return await self.page.screenshot(full_page=True)

    async def get_page_state(self) -> dict:
        """Extract current page state for AI agent."""
        if not self.page:
            raise RuntimeError("Session not started")

        # Get page title and URL
        title = await self.page.title()
        url = self.page.url

        # Extract visible text content
        text_content = await self.page.evaluate("""
            () => {
                const body = document.body;
                return body ? body.innerText : '';
            }
        """)

        # Get interactive elements
        interactive = await self.page.evaluate("""
            () => {
                const elements = [];

                // Buttons
                document.querySelectorAll('button').forEach((el, idx) => {
                    if (el.offsetParent !== null) {
                        elements.push({
                            type: 'button',
                            text: el.innerText.trim(),
                            id: el.id,
                            name: el.name,
                            selector: `button:nth-of-type(${idx + 1})`
                        });
                    }
                });

                // Links
                document.querySelectorAll('a[href]').forEach((el, idx) => {
                    if (el.offsetParent !== null) {
                        elements.push({
                            type: 'link',
                            text: el.innerText.trim(),
                            href: el.href,
                            selector: `a:nth-of-type(${idx + 1})`
                        });
                    }
                });

                // Input fields
                document.querySelectorAll('input, textarea').forEach((el, idx) => {
                    if (el.offsetParent !== null) {
                        elements.push({
                            type: 'input',
                            inputType: el.type,
                            placeholder: el.placeholder,
                            id: el.id,
                            name: el.name,
                            selector: el.id ? `#${el.id}` : `input:nth-of-type(${idx + 1})`
                        });
                    }
                });

                return elements.slice(0, 50); // Limit to first 50 elements
            }
        """)

        return {
            "url": url,
            "title": title,
            "text_content": text_content[:2000],  # Limit text to avoid token overflow
            "interactive_elements": interactive,
        }

    async def close(self, save_trace: bool = False, trace_path: Optional[Path] = None) -> None:
        """Close browser session and optionally save trace."""
        if self.context:
            if save_trace and trace_path:
                trace_path.parent.mkdir(parents=True, exist_ok=True)
                await self.context.tracing.stop(path=str(trace_path))
            else:
                await self.context.tracing.stop()

            await self.context.close()
            self.context = None
            self.page = None
