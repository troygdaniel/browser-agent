"""Browser manager for creating and managing browser instances."""

import asyncio
from pathlib import Path
from typing import Dict, Optional
from playwright.async_api import async_playwright, Playwright, Browser

from .session import BrowserSession


class BrowserManager:
    """Manages browser instances and sessions."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.sessions: Dict[str, BrowserSession] = {}

    async def start(self) -> None:
        """Initialize Playwright and launch browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            channel="chrome",  # Use installed Chrome
        )

    async def create_session(
        self,
        session_id: str,
        profile_dir: Optional[Path] = None,
    ) -> BrowserSession:
        """Create a new isolated browser session."""
        if not self.browser:
            raise RuntimeError("Browser not started")

        session = BrowserSession(
            browser=self.browser,
            session_id=session_id,
            headless=self.headless,
            profile_dir=profile_dir,
        )
        await session.start()
        self.sessions[session_id] = session
        return session

    async def get_session(self, session_id: str) -> Optional[BrowserSession]:
        """Get existing session by ID."""
        return self.sessions.get(session_id)

    async def close_session(self, session_id: str, save_trace: bool = False) -> None:
        """Close a specific session."""
        session = self.sessions.get(session_id)
        if session:
            trace_path = Path(f"traces/{session_id}.zip") if save_trace else None
            await session.close(save_trace=save_trace, trace_path=trace_path)
            del self.sessions[session_id]

    async def close_all(self) -> None:
        """Close all sessions and browser."""
        for session_id in list(self.sessions.keys()):
            await self.close_session(session_id)

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
