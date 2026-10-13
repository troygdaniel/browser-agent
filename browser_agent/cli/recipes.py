"""Recipe management CLI commands."""

from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
import yaml

from ..recipes.storage import RecipeStorage

app = typer.Typer(help="Manage saved automation recipes")
console = Console()


@app.command("list")
def list_recipes():
    """List all saved recipes."""
    storage = RecipeStorage()
    recipes = storage.list_all()

    if not recipes:
        console.print("[yellow]No recipes found. Run a task with AI to create one![/yellow]")
        return

    table = Table(title="Saved Recipes")
    table.add_column("Slug", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Steps", justify="right")
    table.add_column("Success", justify="right", style="green")
    table.add_column("Fails", justify="right", style="red")
    table.add_column("Avg Time", justify="right")
    table.add_column("Last Run")

    for recipe in recipes:
        table.add_row(
            recipe.slug,
            recipe.name[:40],
            str(len(recipe.steps)),
            str(recipe.success_count),
            str(recipe.failure_count),
            f"{recipe.avg_duration_seconds:.1f}s" if recipe.avg_duration_seconds > 0 else "-",
            recipe.last_run.strftime("%Y-%m-%d") if recipe.last_run else "Never",
        )

    console.print(table)
    console.print(f"\n[dim]Run with: browser-agent run <slug>[/dim]")


@app.command("show")
def show_recipe(slug: str = typer.Argument(..., help="Recipe slug")):
    """Show recipe details."""
    storage = RecipeStorage()
    recipe = storage.load(slug)

    if not recipe:
        console.print(f"[red]Recipe '{slug}' not found[/red]")
        return

    # Header
    console.print(Panel.fit(
        f"[bold cyan]{recipe.name}[/bold cyan]\n\n"
        f"{recipe.description}\n\n"
        f"[dim]Created: {recipe.created.strftime('%Y-%m-%d %H:%M')}[/dim]\n"
        f"[dim]Last updated: {recipe.last_updated.strftime('%Y-%m-%d %H:%M')}[/dim]",
        title="Recipe Details",
        border_style="cyan",
    ))

    # Variables
    if recipe.variables:
        console.print("\n[bold]Variables:[/bold]")
        for var in recipe.variables:
            required = "[red]*required[/red]" if var.required else "[dim]optional[/dim]"
            console.print(
                f"  --{var.name}  {required}  "
                f"[dim]{var.description or var.type}[/dim]"
            )
            if var.example:
                console.print(f"    [dim]Example: {var.example}[/dim]")

    # Steps
    console.print("\n[bold]Steps:[/bold]")
    for i, step in enumerate(recipe.steps, 1):
        desc = step.description or step.action
        console.print(f"  {i}. {desc}")
        if step.selector:
            console.print(f"     [dim]Selector: {step.selector}[/dim]")

    # Statistics
    console.print("\n[bold]Statistics:[/bold]")
    total_runs = recipe.success_count + recipe.failure_count
    success_rate = (recipe.success_count / total_runs * 100) if total_runs > 0 else 0
    console.print(f"  Total runs: {total_runs}")
    console.print(f"  Success rate: {success_rate:.1f}%")
    console.print(f"  Average duration: {recipe.avg_duration_seconds:.1f}s")

    # Usage
    console.print("\n[bold]Usage:[/bold]")
    if recipe.variables:
        var_examples = " ".join([f"--{v.name} {v.example or 'value'}" for v in recipe.variables])
        console.print(f"  browser-agent run {recipe.slug} {var_examples}")
    else:
        console.print(f"  browser-agent run {recipe.slug}")


@app.command("delete")
def delete_recipe(slug: str = typer.Argument(..., help="Recipe slug")):
    """Delete a saved recipe."""
    storage = RecipeStorage()

    if not storage.exists(slug):
        console.print(f"[red]Recipe '{slug}' not found[/red]")
        return

    # Confirm deletion
    confirm = typer.confirm(f"Delete recipe '{slug}'?")
    if not confirm:
        console.print("[yellow]Cancelled[/yellow]")
        return

    storage.delete(slug)
    console.print(f"[green]✓ Recipe '{slug}' deleted[/green]")


@app.command("export")
def export_recipe(
    slug: str = typer.Argument(..., help="Recipe slug"),
    output: str = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Export recipe as YAML."""
    storage = RecipeStorage()
    recipe = storage.load(slug)

    if not recipe:
        console.print(f"[red]Recipe '{slug}' not found[/red]")
        return

    yaml_content = yaml.dump(recipe.to_yaml_dict(), default_flow_style=False, sort_keys=False)

    if output:
        with open(output, "w") as f:
            f.write(yaml_content)
        console.print(f"[green]✓ Recipe exported to {output}[/green]")
    else:
        syntax = Syntax(yaml_content, "yaml", theme="monokai")
        console.print(syntax)


@app.command("search")
def search_recipes(query: str = typer.Argument(..., help="Search query")):
    """Search recipes by name, description, or tags."""
    storage = RecipeStorage()
    results = storage.search(query)

    if not results:
        console.print(f"[yellow]No recipes found matching '{query}'[/yellow]")
        return

    console.print(f"[bold]Found {len(results)} recipe(s) matching '{query}':[/bold]\n")

    for recipe in results:
        console.print(f"  [cyan]{recipe.slug}[/cyan] - {recipe.name}")
        console.print(f"    {recipe.description}")
        console.print(f"    [dim]{len(recipe.steps)} steps, {recipe.success_count} successes[/dim]\n")
