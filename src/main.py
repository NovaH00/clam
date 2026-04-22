from typing import Annotated

import typer
from click.shell_completion import CompletionItem
from click import Context, Parameter
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.shell_command import ShellCommand
from src.manager import ShellCommandManager
from src.config import CONFIG_FILE
from src.errors import CommandAlreadyExists, CommandNotFound

command_manager = ShellCommandManager()
app = typer.Typer()


@app.command()
def add():
    """Add a new alias interactively."""
    name = typer.prompt("Name")
    alias = typer.prompt("Alias")
    description = typer.prompt("Description")
    try:
        command_manager.add(ShellCommand(name, alias, description))
        typer.secho(f"Added alias: {name}", fg=typer.colors.GREEN)
    except CommandAlreadyExists:
        typer.secho(f"Error: Alias '{name}' already exists", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@app.command()
def remove(
    name: Annotated[str, typer.Argument(help="Name of the alias to remove")],
):
    """Remove an alias."""
    try:
        command_manager.remove(name)
        typer.secho(f"Removed alias: {name}", fg=typer.colors.GREEN)
    except CommandNotFound:
        typer.secho(f"Error: Alias '{name}' not found", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

def complete_commands(
    ctx: Context,
    param: Parameter,
    incomplete: str
) -> list[str]:
    shell_commands = command_manager.show()

    return [
        cmd.name
        for cmd in shell_commands
        if cmd.name.startswith(incomplete)
    ]

@app.command()
def run(
    name: str | None = typer.Argument(
        default=None, 
        help="Name of the alias to run",
        shell_complete=complete_commands
    )
):
    """Run an alias."""
    if name is None:
        commands = command_manager.show()
        if not commands:
            typer.echo("No aliases available")
            return

        console = Console()
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Name", style="cyan bold", no_wrap=True)
        table.add_column("Description")

        for cmd in commands:
            table.add_row(cmd.name, cmd.description)

        panel = Panel(table, title="Commands", title_align="left", border_style="dim", box=box.ROUNDED)
        console.print(panel)
        return
    try:
        command = command_manager.get(name)
        typer.secho(f"> {command.command}", fg=typer.colors.CYAN) 
        command.run()
    except CommandNotFound:
        typer.secho(f"Error: Alias '{name}' not found", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

@app.command()
def show():
    """List all aliases."""
    commands = command_manager.show()
    if not commands:
        typer.echo("No aliases found")
        return

    console = Console()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Name", style="cyan bold", no_wrap=True)
    table.add_column("Alias", style="dim")
    table.add_column("Description")

    for cmd in commands:
        table.add_row(cmd.name, cmd.command, cmd.description)

    panel = Panel(table, title="Aliases", title_align="left", border_style="dim", box=box.ROUNDED)
    console.print(panel)

@app.command()
def replace(
    name: Annotated[str, typer.Argument(help="Name of the alias to replace")],
    alias: Annotated[str, typer.Argument(help="New alias")],
    description: Annotated[str, typer.Argument(help="New description")],
):
    """Replace an existing alias."""
    try:
        command_manager.replace(ShellCommand(name, alias, description))
        typer.secho(f"Replaced alias: {name}", fg=typer.colors.GREEN)
    except CommandNotFound:
        typer.secho(f"Error: Alias '{name}' not found", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    command_manager.load(CONFIG_FILE)
    try:
        app()
    finally:
        command_manager.save(CONFIG_FILE)
