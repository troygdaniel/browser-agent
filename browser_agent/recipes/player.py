"""Recipe player for fast, deterministic execution."""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from ..browser.session import BrowserSession
from ..agent.ollama import OllamaClient
from .models import Recipe, RecipeStep


class RecipePlayer:
    """Executes saved recipes quickly without AI."""

    def __init__(
        self,
        session: BrowserSession,
        ollama: Optional[OllamaClient] = None,  # For self-healing
        screenshots_dir: Optional[Path] = None,
    ):
        self.session = session
        self.ollama = ollama
        self.screenshots_dir = screenshots_dir
        self.step_count = 0
        self.start_time: Optional[datetime] = None

    async def execute_recipe(
        self, recipe: Recipe, variables: Optional[Dict[str, Any]] = None
    ) -> dict:
        """Execute a recipe with optional variable substitution."""
        self.step_count = 0
        self.start_time = datetime.now()

        # Substitute variables
        if variables:
            recipe = recipe.substitute_variables(variables)

        # Validate required variables
        missing_vars = self._check_required_variables(recipe, variables or {})
        if missing_vars:
            return {
                "success": False,
                "result": None,
                "steps": 0,
                "error": f"Missing required variables: {', '.join(missing_vars)}",
                "duration": 0,
            }

        try:
            for step in recipe.steps:
                self.step_count += 1
                print(f"\n  Step {self.step_count}: {step.description or step.action}")

                # Execute step
                success = await self._execute_step(step)

                if not success:
                    # Try self-healing if AI available
                    if self.ollama:
                        print(f"    ⚠️  Step failed, attempting self-heal...")
                        healed = await self._self_heal_step(step, recipe)
                        if not healed:
                            return self._failure_result(f"Step {self.step_count} failed and could not be healed")
                    else:
                        return self._failure_result(f"Step {self.step_count} failed")

                # Wait for validation if specified
                if step.wait_for:
                    await self._wait_for_element(step.wait_for)

            duration = (datetime.now() - self.start_time).total_seconds()

            return {
                "success": True,
                "result": f"Recipe completed successfully in {duration:.1f}s",
                "steps": self.step_count,
                "error": None,
                "duration": duration,
            }

        except Exception as e:
            return self._failure_result(f"Execution error: {str(e)}")

    async def _execute_step(self, step: RecipeStep) -> bool:
        """Execute a single recipe step."""
        page = self.session.page
        if not page:
            raise RuntimeError("No active page")

        try:
            if step.action == "navigate":
                await self.session.navigate(step.url)
                return True

            elif step.action == "click":
                await page.click(step.selector, timeout=10000)
                await asyncio.sleep(0.5)  # Brief pause after click
                return True

            elif step.action == "type":
                # Use text or value (value is for variable substitution)
                text_to_type = step.value if step.value else step.text
                await page.fill(step.selector, text_to_type)
                return True

            elif step.action == "wait":
                await asyncio.sleep(step.seconds or 1.0)
                return True

            elif step.action == "scroll":
                await page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
                await asyncio.sleep(0.5)
                return True

            else:
                print(f"    Warning: Unknown action type {step.action}")
                return False

        except Exception as e:
            print(f"    Failed: {str(e)}")
            return False

    async def _self_heal_step(self, step: RecipeStep, recipe: Recipe) -> bool:
        """Attempt to heal a broken step using AI."""
        # This would use the AI to find the element again
        # and update the recipe with the new selector
        # For now, return False (will implement in next iteration)
        return False

    async def _wait_for_element(self, selector: str, timeout: float = 5.0) -> bool:
        """Wait for element to appear."""
        try:
            await self.session.page.wait_for_selector(selector, timeout=timeout * 1000)
            return True
        except Exception:
            return False

    def _check_required_variables(
        self, recipe: Recipe, provided: Dict[str, Any]
    ) -> list[str]:
        """Check for missing required variables."""
        missing = []
        for var in recipe.variables:
            if var.required and var.name not in provided:
                missing.append(var.name)
        return missing

    def _failure_result(self, error: str) -> dict:
        """Create failure result."""
        duration = 0
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()

        return {
            "success": False,
            "result": None,
            "steps": self.step_count,
            "error": error,
            "duration": duration,
        }
