"""Smart executor that can learn recipes and replay them."""

import asyncio
from typing import Optional
from pathlib import Path
from datetime import datetime

from ..browser.session import BrowserSession
from .ollama import OllamaClient
from .executor import AgentExecutor
from ..recipes.recorder import RecipeRecorder
from ..recipes.player import RecipePlayer
from ..recipes.storage import RecipeStorage
from ..recipes.models import Recipe


class SmartExecutor:
    """Executes tasks using AI or recipes, with automatic learning."""

    def __init__(
        self,
        session: BrowserSession,
        ollama: OllamaClient,
        max_steps: int = 30,
        screenshots_dir: Optional[Path] = None,
        recipes_dir: Path = Path("recipes"),
    ):
        self.session = session
        self.ollama = ollama
        self.max_steps = max_steps
        self.screenshots_dir = screenshots_dir
        self.storage = RecipeStorage(recipes_dir)

    async def execute_task(
        self,
        task_description: str,
        variables: Optional[dict] = None,
        force_ai: bool = False,
    ) -> dict:
        """Execute task using recipe if available, otherwise use AI and learn."""

        # Check if we have a matching recipe
        if not force_ai:
            recipe = self._find_matching_recipe(task_description)
            if recipe:
                print(f"\n  📖 Using saved recipe: {recipe.name}")
                print(f"  ⚡ Fast execution mode (avg: {recipe.avg_duration_seconds:.1f}s)")

                result = await self._execute_recipe(recipe, variables)

                # Update statistics
                if result["success"]:
                    await self._update_recipe_stats(recipe, result["duration"], True)
                else:
                    await self._update_recipe_stats(recipe, result["duration"], False)

                return result

        # No recipe found, use AI and record
        print(f"\n  🤖 Learning mode - AI will figure this out and save a recipe")

        result = await self._execute_with_ai_and_record(task_description, variables)

        return result

    async def _execute_recipe(self, recipe: Recipe, variables: Optional[dict]) -> dict:
        """Execute using saved recipe."""
        player = RecipePlayer(
            session=self.session,
            ollama=self.ollama,  # For self-healing
            screenshots_dir=self.screenshots_dir,
        )

        result = await player.execute_recipe(recipe, variables)

        # Update last_run
        recipe.last_run = datetime.now()
        self.storage.save(recipe)

        return result

    async def _execute_with_ai_and_record(
        self, task_description: str, variables: Optional[dict]
    ) -> dict:
        """Execute with AI and record steps as recipe."""

        # Create AI executor with modified behavior to track actions
        from .executor import AgentExecutor
        from .actions import Action

        executor = AgentExecutor(
            session=self.session,
            ollama=self.ollama,
            max_steps=self.max_steps,
            screenshots_dir=self.screenshots_dir,
        )

        # Monkey-patch executor to capture actions
        recorder = RecipeRecorder(task_description)
        original_execute_action = executor._execute_action

        async def recording_execute_action(action: Action) -> bool:
            result = await original_execute_action(action)
            if result:  # Only record successful actions
                recorder.record_action(action, success=True)
            return result

        executor._execute_action = recording_execute_action

        # Execute with AI
        result = await executor.execute_task(task_description)

        # If successful and has multiple steps, save recipe
        if result["success"] and result["steps"] >= 2:
            recipe = recorder.generate_recipe()

            print(f"\n  ✅ Task completed successfully in {result['steps']} steps!")
            print(f"\n  💾 Saving as recipe for faster future execution...")
            print(f"     Name: {recipe.name}")
            print(f"     Slug: {recipe.slug}")

            self.storage.save(recipe)
            print(f"  ✅ Recipe saved! Next time run: browser-agent run {recipe.slug}")

            if recipe.variables:
                vars_example = " ".join([f"--{v.name} {v.example}" for v in recipe.variables])
                print(f"     With variables: browser-agent run {recipe.slug} {vars_example}")

        return result

    def _find_matching_recipe(self, task_description: str) -> Optional[Recipe]:
        """Find a recipe that matches the task description."""
        # Simple keyword matching for now
        # Will improve with fuzzy matching or embeddings later

        task_lower = task_description.lower()

        # Try exact slug match first
        words = task_lower.split()
        for word in words:
            recipe = self.storage.load(word)
            if recipe:
                return recipe

        # Try searching
        results = self.storage.search(task_description)
        if results:
            # Return best match (first result for now)
            return results[0]

        return None

    async def _update_recipe_stats(
        self, recipe: Recipe, duration: float, success: bool
    ) -> None:
        """Update recipe execution statistics."""
        if success:
            recipe.success_count += 1
            # Update rolling average
            total_runs = recipe.success_count + recipe.failure_count
            recipe.avg_duration_seconds = (
                recipe.avg_duration_seconds * (total_runs - 1) + duration
            ) / total_runs
        else:
            recipe.failure_count += 1

        recipe.last_updated = datetime.now()
        self.storage.save(recipe)
