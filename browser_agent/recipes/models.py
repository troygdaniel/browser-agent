"""Recipe data models."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class RecipeVariable(BaseModel):
    """A variable that can be substituted in recipe steps."""

    name: str
    type: str = "string"  # string, number, date, etc.
    description: Optional[str] = None
    example: Optional[str] = None
    required: bool = True


class RecipeStep(BaseModel):
    """A single step in a recipe."""

    action: str  # navigate, click, type, wait, scroll, complete
    description: Optional[str] = None

    # Action-specific fields
    url: Optional[str] = None
    selector: Optional[str] = None
    text: Optional[str] = None
    value: Optional[str] = None  # For variable substitution
    seconds: Optional[float] = None

    # Validation
    wait_for: Optional[str] = None  # Selector to wait for after action
    expect_text: Optional[str] = None  # Text that should appear

    # Self-healing metadata
    original_selector: Optional[str] = None  # For tracking selector changes
    last_updated: Optional[datetime] = None


class Recipe(BaseModel):
    """A saved automation recipe."""

    name: str
    slug: str  # URL-safe name for CLI
    description: str
    created: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    last_run: Optional[datetime] = None

    # Usage statistics
    success_count: int = 0
    failure_count: int = 0
    avg_duration_seconds: float = 0.0

    # Recipe definition
    variables: List[RecipeVariable] = []
    steps: List[RecipeStep] = []

    # Metadata
    tags: List[str] = []
    url_pattern: Optional[str] = None  # e.g., "*.service-now.com"

    def to_yaml_dict(self) -> dict:
        """Convert to YAML-friendly dict."""
        return {
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "created": self.created.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "avg_duration_seconds": self.avg_duration_seconds,
            "tags": self.tags,
            "url_pattern": self.url_pattern,
            "variables": [
                {
                    "name": v.name,
                    "type": v.type,
                    "description": v.description,
                    "example": v.example,
                    "required": v.required,
                }
                for v in self.variables
            ],
            "steps": [
                {k: v for k, v in step.model_dump().items() if v is not None}
                for step in self.steps
            ],
        }

    @classmethod
    def from_yaml_dict(cls, data: dict) -> "Recipe":
        """Create from YAML dict."""
        # Convert ISO strings back to datetime
        if "created" in data and isinstance(data["created"], str):
            data["created"] = datetime.fromisoformat(data["created"])
        if "last_updated" in data and isinstance(data["last_updated"], str):
            data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        if "last_run" in data and isinstance(data["last_run"], str):
            data["last_run"] = datetime.fromisoformat(data["last_run"])

        # Convert variables
        if "variables" in data:
            data["variables"] = [RecipeVariable(**v) for v in data["variables"]]

        # Convert steps
        if "steps" in data:
            # Handle datetime in steps
            for step in data["steps"]:
                if "last_updated" in step and isinstance(step["last_updated"], str):
                    step["last_updated"] = datetime.fromisoformat(step["last_updated"])
            data["steps"] = [RecipeStep(**s) for s in data["steps"]]

        return cls(**data)

    def substitute_variables(self, values: Dict[str, Any]) -> "Recipe":
        """Create a new recipe with variables substituted."""
        import copy
        recipe = copy.deepcopy(self)

        for step in recipe.steps:
            # Substitute in text/value fields
            if step.text:
                step.text = self._substitute(step.text, values)
            if step.value:
                step.value = self._substitute(step.value, values)
            if step.url:
                step.url = self._substitute(step.url, values)

        return recipe

    def _substitute(self, text: str, values: Dict[str, Any]) -> str:
        """Substitute {{variable}} patterns."""
        import re

        def replacer(match):
            var_name = match.group(1)
            return str(values.get(var_name, match.group(0)))

        return re.sub(r'\{\{(\w+)\}\}', replacer, text)
