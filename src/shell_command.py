import subprocess
import sys
import threading
import time
from typing import BinaryIO, cast

class ShellCommand:
    def __init__(
        self,
        name: str,
        command: str,
        description: str
    ):
        self.name = name
        self.command = command
        self.description = description

    def run(self) -> int:
        process = subprocess.Popen(
            self.command,
            shell=True,
            executable="/bin/bash"
        )

        process.wait()

        return process.returncode
