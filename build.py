import subprocess
import sys
import shutil
import os
from pathlib import Path

def main():
    if not shutil.which("nuitka"):
        print("Error: nuitka not found", file=sys.stderr)
        sys.exit(1)

    args = [
        "nuitka",
        "--mode=onefile",
        "--output-dir=dist",
        "--output-filename=clam",
        "--python-flag=isolated",
        "--include-package=orjson",
        "--include-package=platformdirs",
        "--include-package=typer",
        "--include-package=rich",
        "--include-package-data=typer",
        "--include-package-data=rich",
        "src/main.py",
    ]

    sys.exit(subprocess.call(args))

if __name__ == "__main__":
    main()
