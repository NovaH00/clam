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

    def _stream_reader(self, stream: BinaryIO, stream_name: str):
        """Function run in a separate thread to continuously read from a stream."""
        if stream_name == "stdout":
            out_stream = cast(BinaryIO, sys.stdout.buffer)
        else:
            out_stream = cast(BinaryIO, sys.stderr.buffer)

        while True:
            line = stream.readline()
            if not line:
                break

            out_stream.write(line)
            out_stream.flush()

    def run(self) -> int:
        process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            shell=True
        )

        # 1. Create threads for simultaneous reading
        stdout_thread = threading.Thread(
            target=self._stream_reader,
            args=(process.stdout, "stdout")
        )
        stderr_thread = threading.Thread(
            target=self._stream_reader,
            args=(process.stderr, "stderr")
        )

        # 2. Start the threads
        stdout_thread.start()
        stderr_thread.start()

        # 3. Wait for the process to finish
        process.wait()

        # 4. Wait for the reader threads to finish consuming all remaining data
        stdout_thread.join()
        stderr_thread.join()

        return process.returncode
