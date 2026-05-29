import os
import sys
from pathlib import Path
from typing import Annotated

import typer
import click
from click import Context, Parameter
from click.shell_completion import CompletionItem
from typer.main import get_command
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.shell_command import ShellCommand
from src.manager import ShellCommandManager
from src.config import CONFIG_FILE
from src.errors import CommandAlreadyExists, CommandNotFound

command_manager = ShellCommandManager()

def _run_alias(name: str) -> None:
    command = command_manager.get(name)
    typer.secho(f"> {command.command}", fg=typer.colors.CYAN)
    command.run()

def _show_aliases() -> None:
    commands = command_manager.show()
    if not commands:
        typer.echo("No aliases available")
        return

    console = Console()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Name", style="green bold", no_wrap=True)
    table.add_column("Description", style="italic")

    for cmd in commands:
        table.add_row(cmd.name, cmd.description)

    panel = Panel(table, title="Available aliases", title_align="left", border_style="dim", box=box.ROUNDED)
    console.print(panel)

def _show_commands() -> None:
    commands = sorted(app._command_names)
    descriptions = {
        cmd.name or cmd.callback.__name__.lower().replace("_", "-"): cmd.callback.__doc__
        for cmd in app.registered_commands
    }
    console = Console()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Name", style="cyan bold", no_wrap=True)
    table.add_column("Description", style="italic")

    for cmd in commands:
        table.add_row(cmd, descriptions.get(cmd, ""))

    panel = Panel(table, title="Available commands", title_align="left", border_style="dim", box=box.ROUNDED)
    console.print(panel)

class AliasedTyper(typer.Typer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._help_template: str | None = None

    @property
    def _command_names(self) -> set[str]:
        names = set()
        for cmd in self.registered_commands:
            names.add(cmd.name or cmd.callback.__name__.lower().replace("_", "-"))
        for grp in self.registered_groups:
            names.add(grp.name)
        if self.registered_callback and self.registered_callback.name:
            names.add(self.registered_callback.name)
        return names

    def _get_group(self) -> click.Group:
        group = get_command(self)
        original_complete = group.shell_complete

        def patched_shell_complete(ctx, incomplete):
            items = original_complete(ctx, incomplete)
            existing = {i.value for i in items}
            for alias in command_manager.show():
                if alias.name.startswith(incomplete) and alias.name not in existing:
                    items.append(CompletionItem(alias.name, help=alias.description))
            return items

        group.shell_complete = patched_shell_complete
        return group

    def __call__(self, *args, **kwargs):
        prog_name = getattr(self, 'name', None) or os.path.basename(sys.argv[0])
        complete_var = f"_{prog_name}_COMPLETE".replace("-", "_").upper()
        if complete_var in os.environ:
            return self._get_group()(*args, **kwargs)

        if self.registered_callback and self.registered_callback.callback:
            if self._help_template is None:
                self._help_template = self.registered_callback.callback.__doc__ or ""
            self.registered_callback.callback.__doc__ = self._help_template.replace("{prog}", Path(sys.argv[0]).name)

        raw_args = args[0] if args else None
        if raw_args is None:
            raw_args = sys.argv[1:]
        elif isinstance(raw_args, str):
            raw_args = [raw_args]

        raw_args = list(raw_args)

        if not raw_args:
            _show_commands()
            _show_aliases()
            typer.echo("\nUse --help for more information about available commands.")
            return

        if raw_args[0].startswith("-"):
            return self._get_group()(*args, **kwargs)

        if raw_args[0] not in self._command_names:
            try:
                command_manager.get(raw_args[0])
                _run_alias(raw_args[0])
                return
            except CommandNotFound:
                _show_commands()
                _show_aliases()
                typer.echo("\nUse --help for more information about available commands.")
                sys.exit(1)

        return self._get_group()(*args, **kwargs)

app = AliasedTyper()

@app.callback()
def main():
    """
    CLAM - Command Line Alias Manager

    Run an alias directly: [bold]{prog} <alias>[/bold]
    """

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
def add():
    """Add a new alias interactively."""
    name = typer.prompt("Name")
    if name.lower() in app._command_names:
        typer.secho(f"Error: '{name}' is a reserved command name", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
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
    name: str = typer.Argument(
        help="Name of the alias to remove",
        shell_complete=complete_commands
    )
):
    """Remove an alias."""
    try:
        command_manager.remove(name)
        typer.secho(f"Removed alias: {name}", fg=typer.colors.GREEN)
    except CommandNotFound:
        typer.secho(f"Error: Alias '{name}' not found", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

@app.command()
def show(
    name: str | None = typer.Argument(
        default=None, 
        help="Name of the alias to show",
        shell_complete=complete_commands
    )
):
    """List all aliases."""
    commands = command_manager.show()
    if not commands:
        typer.echo("No aliases found")
        return

    console = Console()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Name", style="green bold", no_wrap=True)
    table.add_column("Alias")
    table.add_column("Description", style="italic")

    if name is None:
        for cmd in commands:
            table.add_row(cmd.name, cmd.command, cmd.description)
            table.add_row();
    else:
        try:
            cmd = command_manager.get(name)
        except CommandNotFound:
            typer.secho(f"Alias `{name}` not found")

        table.add_row(cmd.name, cmd.command, cmd.description)

    panel = Panel(table, title="Aliases", title_align="left", border_style="dim", box=box.ROUNDED)
    console.print(panel)

@app.command()
def replace(
    name: str = typer.Argument(
        help="Name of the alias to replace",
        shell_complete=complete_commands
    ),
):
    """Replace an existing alias."""
    try:
        existing = command_manager.get(name)
    except CommandNotFound:
        typer.secho(f"Error: Alias '{name}' not found", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    console = Console()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="bold")
    table.add_column("Value", style="dim")
    table.add_row("Name", existing.name)
    table.add_row("Alias", existing.command)
    table.add_row("Description", existing.description)
    panel = Panel(table, title=f"Current: {name}", title_align="left", border_style="dim", box=box.ROUNDED)
    console.print(panel)

    new_name = typer.prompt("New Name", default=existing.name) or existing.name
    new_alias = typer.prompt("New Alias", default=existing.command) or existing.command
    new_description = typer.prompt("New Description", default=existing.description) or existing.description

    command_manager.replace(ShellCommand(new_name, new_alias, new_description), old_name=name)
    typer.secho(f"Replaced alias: {name}", fg=typer.colors.GREEN)

if __name__ == "__main__":
    command_manager.load(CONFIG_FILE)
    try:
        app()
    finally:
        command_manager.save(CONFIG_FILE)
