"""Recipe recorder that captures AI steps."""

import re
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..agent.actions import Action, ActionType
from .models import Recipe, RecipeStep, RecipeVariable


class RecipeRecorder:
    """Records AI execution steps as a reusable recipe."""

    def __init__(self, task_description: str):
        self.task_description = task_description
        self.steps: List[RecipeStep] = []
        self.detected_variables: Dict[str, Any] = {}

    def record_action(self, action: Action, success: bool = True) -> None:
        """Record an action as a recipe step."""
        if not success:
            return  # Only record successful actions

        if action.type == ActionType.NAVIGATE:
            self.steps.append(
                RecipeStep(
                    action="navigate",
                    url=action.url,
                    description=f"Navigate to {action.url}",
                )
            )

        elif action.type == ActionType.CLICK:
            self.steps.append(
                RecipeStep(
                    action="click",
                    selector=action.selector,
                    description=f"Click {action.selector}",
                    original_selector=action.selector,
                    last_updated=datetime.now(),
                )
            )

        elif action.type == ActionType.TYPE:
            # Check if this looks like a variable (numbers, dates, etc.)
            var_name = self._detect_variable(action.text, action.selector)

            if var_name:
                # Store as variable
                self.steps.append(
                    RecipeStep(
                        action="type",
                        selector=action.selector,
                        value=f"{{{{{var_name}}}}}",  # {{variable}}
                        description=f"Enter {var_name}",
                        original_selector=action.selector,
                        last_updated=datetime.now(),
                    )
                )
                self.detected_variables[var_name] = action.text
            else:
                # Store as literal
                self.steps.append(
                    RecipeStep(
                        action="type",
                        selector=action.selector,
                        text=action.text,
                        description=f"Type '{action.text[:30]}...'",
                        original_selector=action.selector,
                        last_updated=datetime.now(),
                    )
                )

        elif action.type == ActionType.WAIT:
            self.steps.append(
                RecipeStep(
                    action="wait",
                    seconds=action.seconds or 1.0,
                    description="Wait briefly",
                )
            )

        elif action.type == ActionType.SCROLL:
            self.steps.append(
                RecipeStep(
                    action="scroll",
                    description="Scroll down page",
                )
            )

    def _detect_variable(self, text: str, selector: str) -> Optional[str]:
        """Detect if text looks like a variable value."""
        # Check for common variable patterns
        patterns = {
            r'^CHG\d+$': 'chg_number',
            r'^\d{4}-\d{2}-\d{2}$': 'date',
            r'^\d+$': self._guess_number_var(selector),
            r'^[A-Z]{2,}\d+$': 'reference_number',
        }

        for pattern, var_name in patterns.items():
            if re.match(pattern, text):
                return var_name

        return None

    def _guess_number_var(self, selector: str) -> str:
        """Guess variable name from selector."""
        selector_lower = selector.lower()

        if 'amount' in selector_lower or 'price' in selector_lower:
            return 'amount'
        elif 'quantity' in selector_lower or 'count' in selector_lower:
            return 'quantity'
        elif 'id' in selector_lower:
            return 'id_number'
        else:
            return 'number'

    def generate_recipe(self, task_name: Optional[str] = None) -> Recipe:
        """Generate a recipe from recorded steps."""
        # Create slug from task description or name
        if task_name:
            name = task_name
        else:
            name = self.task_description[:50]

        slug = self._slugify(name)

        # Create variables from detected values
        variables = []
        for var_name, example_value in self.detected_variables.items():
            variables.append(
                RecipeVariable(
                    name=var_name,
                    type=self._infer_type(example_value),
                    example=str(example_value),
                    description=f"The {var_name.replace('_', ' ')}",
                )
            )

        return Recipe(
            name=name,
            slug=slug,
            description=self.task_description,
            variables=variables,
            steps=self.steps,
            created=datetime.now(),
            last_updated=datetime.now(),
        )

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        # Remove special characters, convert to lowercase, replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

    def _infer_type(self, value: Any) -> str:
        """Infer variable type from example value."""
        if isinstance(value, int):
            return "number"
        elif isinstance(value, float):
            return "decimal"
        elif re.match(r'^\d{4}-\d{2}-\d{2}$', str(value)):
            return "date"
        else:
            return "string"
