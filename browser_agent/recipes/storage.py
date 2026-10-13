"""Recipe storage and management."""

from pathlib import Path
from typing import List, Optional
import yaml

from .models import Recipe


class RecipeStorage:
    """Manages recipe storage in YAML files."""

    def __init__(self, recipes_dir: Path = Path("recipes")):
        self.recipes_dir = recipes_dir
        self.recipes_dir.mkdir(parents=True, exist_ok=True)

    def save(self, recipe: Recipe) -> Path:
        """Save recipe to YAML file."""
        file_path = self.recipes_dir / f"{recipe.slug}.yaml"

        with open(file_path, "w") as f:
            yaml.dump(recipe.to_yaml_dict(), f, default_flow_style=False, sort_keys=False)

        return file_path

    def load(self, slug: str) -> Optional[Recipe]:
        """Load recipe by slug."""
        file_path = self.recipes_dir / f"{slug}.yaml"

        if not file_path.exists():
            return None

        with open(file_path) as f:
            data = yaml.safe_load(f)

        return Recipe.from_yaml_dict(data)

    def list_all(self) -> List[Recipe]:
        """List all saved recipes."""
        recipes = []

        for file_path in self.recipes_dir.glob("*.yaml"):
            try:
                with open(file_path) as f:
                    data = yaml.safe_load(f)
                recipes.append(Recipe.from_yaml_dict(data))
            except Exception as e:
                print(f"Warning: Could not load {file_path}: {e}")

        return sorted(recipes, key=lambda r: r.last_updated, reverse=True)

    def delete(self, slug: str) -> bool:
        """Delete recipe by slug."""
        file_path = self.recipes_dir / f"{slug}.yaml"

        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def exists(self, slug: str) -> bool:
        """Check if recipe exists."""
        file_path = self.recipes_dir / f"{slug}.yaml"
        return file_path.exists()

    def search(self, query: str) -> List[Recipe]:
        """Search recipes by name, description, or tags."""
        query = query.lower()
        results = []

        for recipe in self.list_all():
            if (
                query in recipe.name.lower()
                or query in recipe.description.lower()
                or any(query in tag.lower() for tag in recipe.tags)
            ):
                results.append(recipe)

        return results
