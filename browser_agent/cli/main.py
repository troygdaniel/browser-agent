"""Main CLI application."""

import asyncio
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from ..browser.manager import BrowserManager
from ..agent.ollama import OllamaClient
from ..agent.executor import AgentExecutor
from ..tasks.models import Task
from ..config.profiles import load_config

app = typer.Typer(help="Browser Agent - Local AI-powered browser automation")
console = Console()


@app.command()
def run(
    task: str = typer.Argument(..., help="Task description in natural language"),
    url: Optional[str] = typer.Option(None, "--url", help="Starting URL"),
    headed: bool = typer.Option(False, "--headed", help="Run browser in visible mode"),
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode"),
    profile: str = typer.Option("home", "--profile", help="Configuration profile (home/work)"),
    max_steps: int = typer.Option(30, "--max-steps", help="Maximum steps before stopping"),
):
    """Run a browser automation task."""

    # Determine headless mode
    if headed:
        headless_mode = False
    elif headless:
        headless_mode = True
    else:
        # Default: headed for better visibility during development
        headless_mode = False

    # Load configuration
    config = load_config(profile)
    config.browser.headless = headless_mode

    # Run async task
    asyncio.run(_run_task(task, url, config, max_steps))


async def _run_task(task_description: str, start_url: Optional[str], config, max_steps: int):
    """Execute the browser automation task."""

    # Create task object
    task_obj = Task(description=task_description)
    task_obj.start()

    console.print(Panel.fit(
        f"[bold cyan]Task:[/bold cyan] {task_description}\n"
        f"[bold cyan]Task ID:[/bold cyan] {task_obj.id}\n"
        f"[bold cyan]Mode:[/bold cyan] {'Headless' if config.browser.headless else 'Visible'}",
        title="Browser Agent",
        border_style="cyan",
    ))

    # Check Ollama availability
    console.print("\n[yellow]Checking Ollama...[/yellow]")
    ollama = OllamaClient(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
    )

    if not await ollama.check_health():
        console.print("[red]Error: Ollama is not available at " + config.ollama.base_url + "[/red]")
        console.print("[yellow]Make sure Ollama is running: ollama serve[/yellow]")
        return

    console.print(f"[green]✓ Ollama connected ({config.ollama.model})[/green]")

    # Initialize browser
    console.print("\n[yellow]Starting browser...[/yellow]")
    browser_manager = BrowserManager(headless=config.browser.headless)

    try:
        await browser_manager.start()
        console.print("[green]✓ Browser started[/green]")

        # Create session
        session = await browser_manager.create_session(
            session_id=task_obj.id,
            profile_dir=None,
        )
        task_obj.session_id = session.session_id

        # Navigate to start URL if provided
        if start_url:
            console.print(f"\n[yellow]Navigating to {start_url}...[/yellow]")
            await session.navigate(start_url)
            console.print("[green]✓ Page loaded[/green]")

        # Create executor
        screenshots_dir = config.screenshots_dir / task_obj.id
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        executor = AgentExecutor(
            session=session,
            ollama=ollama,
            max_steps=max_steps,
            screenshots_dir=screenshots_dir,
        )

        # Execute task
        console.print("\n[bold yellow]Executing task...[/bold yellow]")

        result = await executor.execute_task(task_description)

        # Display results
        console.print("\n" + "="*60)
        if result["success"]:
            console.print(Panel.fit(
                f"[bold green]Task Completed Successfully[/bold green]\n\n"
                f"Result: {result['result']}\n"
                f"Steps: {result['steps']}",
                border_style="green",
            ))
            task_obj.complete(result["result"])
        else:
            console.print(Panel.fit(
                f"[bold red]Task Failed[/bold red]\n\n"
                f"Error: {result['error']}\n"
                f"Steps: {result['steps']}",
                border_style="red",
            ))
            task_obj.fail(result["error"])

        # Save trace
        console.print(f"\n[dim]Saving browser trace...[/dim]")
        trace_path = config.traces_dir / f"{task_obj.id}.zip"
        await browser_manager.close_session(task_obj.id, save_trace=True)
        console.print(f"[dim]Trace saved to: {trace_path}[/dim]")

    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        task_obj.fail(str(e))

    finally:
        # Cleanup
        await browser_manager.close_all()
        console.print("[dim]Browser closed[/dim]")


@app.command()
def version():
    """Show version information."""
    from .. import __version__
    console.print(f"Browser Agent v{__version__}")


@app.command()
def check():
    """Check system requirements."""

    async def _check():
        console.print("[bold]Checking System Requirements[/bold]\n")

        # Check Ollama
        ollama = OllamaClient()
        ollama_ok = await ollama.check_health()

        if ollama_ok:
            console.print("[green]✓ Ollama is running[/green]")
        else:
            console.print("[red]✗ Ollama is not available[/red]")
            console.print("[yellow]  Start with: ollama serve[/yellow]")

        # Check models
        console.print(f"\n[bold]Available Models:[/bold]")
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    for model in models:
                        console.print(f"  • {model['name']} ({model.get('size', 'unknown size')})")
                    if not models:
                        console.print("  [yellow]No models installed[/yellow]")
                        console.print("  [dim]Install with: ollama pull deepseek-coder:6.7b[/dim]")
        except Exception as e:
            console.print(f"  [red]Error checking models: {e}[/red]")

        # Check Chrome
        console.print(f"\n[bold]Browser:[/bold]")
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(channel="chrome")
                version = browser.version
                await browser.close()
                console.print(f"[green]✓ Chrome {version}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Chrome not available: {e}[/red]")
            console.print("[yellow]  Install Playwright browsers: playwright install chrome[/yellow]")

    asyncio.run(_check())


if __name__ == "__main__":
    app()
