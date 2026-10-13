"""Agent executor that runs browser automation tasks."""

import asyncio
from typing import Optional
from pathlib import Path

from ..browser.session import BrowserSession
from .ollama import OllamaClient
from .actions import Action, ActionType


class AgentExecutor:
    """Executes browser automation tasks using AI agent."""

    def __init__(
        self,
        session: BrowserSession,
        ollama: OllamaClient,
        max_steps: int = 30,
        screenshots_dir: Optional[Path] = None,
    ):
        self.session = session
        self.ollama = ollama
        self.max_steps = max_steps
        self.screenshots_dir = screenshots_dir
        self.action_history: list[str] = []
        self.step_count = 0
        self.last_action: Optional[Action] = None
        self.repeated_action_count = 0

    async def execute_task(self, task_description: str) -> dict:
        """Execute a browser automation task.

        Returns:
            dict with keys: success, result, steps, error
        """
        self.action_history = []
        self.step_count = 0

        try:
            while self.step_count < self.max_steps:
                self.step_count += 1

                # Get current page state
                page_state = await self.session.get_page_state()

                # Ask AI for next action
                action = await self.ollama.decide_action(
                    task_description=task_description,
                    page_state=page_state,
                    history=self.action_history,
                )

                # Detect repeated actions (loop detection)
                if self.last_action and self._is_same_action(action, self.last_action):
                    self.repeated_action_count += 1
                    if self.repeated_action_count >= 3:
                        # AI is stuck in a loop
                        return {
                            "success": False,
                            "result": None,
                            "steps": self.step_count,
                            "error": "AI stuck in loop - repeated same action 3+ times. Task may need human guidance.",
                        }
                else:
                    self.repeated_action_count = 0

                self.last_action = action

                # Log action
                action_desc = self._action_description(action)
                self.action_history.append(action_desc)
                print(f"\n  Step {self.step_count}: {action_desc}")

                if action.thinking:
                    print(f"    Thinking: {action.thinking}")

                # Execute action
                result = await self._execute_action(action)

                # Check for completion states
                if action.type == ActionType.COMPLETE:
                    return {
                        "success": True,
                        "result": action.result,
                        "steps": self.step_count,
                        "error": None,
                    }

                elif action.type == ActionType.NEEDS_ATTENTION:
                    return {
                        "success": False,
                        "result": None,
                        "steps": self.step_count,
                        "error": f"Needs attention: {action.reason}",
                    }

                elif action.type == ActionType.ERROR:
                    return {
                        "success": False,
                        "result": None,
                        "steps": self.step_count,
                        "error": action.reason,
                    }

                # Small delay between actions
                await asyncio.sleep(0.5)

            # Max steps reached
            return {
                "success": False,
                "result": None,
                "steps": self.step_count,
                "error": f"Max steps ({self.max_steps}) reached without completion",
            }

        except Exception as e:
            return {
                "success": False,
                "result": None,
                "steps": self.step_count,
                "error": f"Execution error: {str(e)}",
            }

    async def _execute_action(self, action: Action) -> bool:
        """Execute a single action via Playwright.

        Returns:
            True if action succeeded, False otherwise
        """
        page = self.session.page
        if not page:
            raise RuntimeError("No active page")

        try:
            if action.type == ActionType.NAVIGATE:
                await self.session.navigate(action.url)
                return True

            elif action.type == ActionType.CLICK:
                await page.click(action.selector, timeout=10000)
                await page.wait_for_load_state("networkidle", timeout=5000)
                return True

            elif action.type == ActionType.TYPE:
                await page.fill(action.selector, action.text)
                return True

            elif action.type == ActionType.WAIT:
                await asyncio.sleep(action.seconds or 1.0)
                return True

            elif action.type == ActionType.SCROLL:
                await page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
                await asyncio.sleep(0.5)
                return True

            elif action.type in (ActionType.COMPLETE, ActionType.NEEDS_ATTENTION, ActionType.ERROR):
                return True

            else:
                print(f"    Warning: Unknown action type {action.type}")
                return False

        except Exception as e:
            print(f"    Action failed: {str(e)}")
            # Try to take screenshot on error if directory provided and page still exists
            if self.screenshots_dir and self.session.page:
                try:
                    screenshot_path = self.screenshots_dir / f"error_step_{self.step_count}.png"
                    await self.session.screenshot(screenshot_path)
                except Exception:
                    pass  # Ignore screenshot errors
            return False

    def _is_same_action(self, action1: Action, action2: Action) -> bool:
        """Check if two actions are the same."""
        if action1.type != action2.type:
            return False
        if action1.type == ActionType.NAVIGATE:
            return action1.url == action2.url
        elif action1.type == ActionType.CLICK:
            return action1.selector == action2.selector
        elif action1.type == ActionType.TYPE:
            return action1.selector == action2.selector
        return False

    def _action_description(self, action: Action) -> str:
        """Generate human-readable action description."""
        if action.type == ActionType.NAVIGATE:
            return f"Navigate to {action.url}"
        elif action.type == ActionType.CLICK:
            return f"Click {action.selector}"
        elif action.type == ActionType.TYPE:
            return f"Type into {action.selector}"
        elif action.type == ActionType.WAIT:
            return f"Wait {action.seconds}s"
        elif action.type == ActionType.SCROLL:
            return "Scroll down"
        elif action.type == ActionType.COMPLETE:
            return f"Complete: {action.result}"
        elif action.type == ActionType.NEEDS_ATTENTION:
            return f"Needs attention: {action.reason}"
        elif action.type == ActionType.ERROR:
            return f"Error: {action.reason}"
        else:
            return f"Unknown action: {action.type}"
