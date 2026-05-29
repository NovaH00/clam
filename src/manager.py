import orjson
import pathlib

from src.shell_command import ShellCommand
from src.errors import CommandAlreadyExists, CommandNotFound, CouldNotLoadConfig 

type CommandName = str
type SerializedShellCommand = dict[str, str]

class ShellCommandManager:
    def __init__(self):
        self._shell_commands: dict[str, ShellCommand] = {}

    def show(self) -> list[ShellCommand]:
        return list(self._shell_commands.values())

    def get(self, name: CommandName) -> ShellCommand:
        if name not in self._shell_commands:
            raise CommandNotFound()
        return self._shell_commands[name]

    def add(self, cmd: ShellCommand):
        if cmd.name in self._shell_commands:
            raise CommandAlreadyExists() 

        self._shell_commands[cmd.name] = cmd

    def remove(self, name: CommandName):
        try:
            del self._shell_commands[name]
        except KeyError:
            raise CommandNotFound()

    def replace(self, new_cmd: ShellCommand, old_name: CommandName | None = None):
        if old_name is not None and old_name != new_cmd.name:
            if old_name in self._shell_commands:
                del self._shell_commands[old_name]
        elif new_cmd.name not in self._shell_commands:
            raise CommandNotFound()

        self._shell_commands[new_cmd.name] = new_cmd

    def serialize(
        self, 
        shell_commands: dict[CommandName, ShellCommand]
    ) -> dict[CommandName, SerializedShellCommand]:
        data: dict[CommandName, SerializedShellCommand] = {} 
        for cmd_name, shell_cmd in shell_commands.items():
            data[cmd_name] = {
                "name": shell_cmd.name,
                "command": shell_cmd.command,
                "description": shell_cmd.description
            } 

        return data

    def deserialize(
        self,
        data: dict[CommandName, SerializedShellCommand]
    ) -> dict[CommandName, ShellCommand]:

        if not isinstance(data, dict):
            raise TypeError("Expected top-level object to be a dict")

        shell_commands: dict[CommandName, ShellCommand] = {}

        for cmd_name, cmd_data in data.items():
            if not isinstance(cmd_name, str):
                raise TypeError("Command name must be a string")

            if not isinstance(cmd_data, dict):
                raise TypeError(f"Command '{cmd_name}' must be an object")

            try:
                name = cmd_data["name"]
                command = cmd_data["command"]
                description = cmd_data["description"]
            except KeyError as e:
                raise KeyError(f"Missing required field: {e.args[0]} in '{cmd_name}'") from e

            if not all(isinstance(x, str) for x in (name, command, description)):
                raise TypeError(f"All fields must be strings in '{cmd_name}'")

            if name != cmd_name:
                raise ValueError(f"Key '{cmd_name}' does not match name '{name}'")

            shell_commands[cmd_name] = ShellCommand(name, command, description)

        return shell_commands

    def load(self, file_path: pathlib.Path) -> None:
        try:
            if not file_path.exists():
                self._shell_commands = {}
                return

            raw = file_path.read_bytes()

            if not raw.strip():  # empty or whitespace-only
                self._shell_commands = {}
                return

            data = orjson.loads(raw)
            self._shell_commands = self.deserialize(data)

        except orjson.JSONDecodeError as e:
            raise CouldNotLoadConfig(
                f"Invalid JSON in config: {file_path}"
            ) from e
        except Exception as e:
            raise CouldNotLoadConfig(
                f"Failed to load commands from {file_path}"
            ) from e

    def save(self, file_path: pathlib.Path) -> None:
        data = self.serialize(self._shell_commands)
        file_path.write_bytes(
            orjson.dumps(data, option=orjson.OPT_INDENT_2)
        )
