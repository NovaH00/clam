# CLAM: Command Line Alias Manager

CLAM lets you manage shell aliases directly from the command line without editing config files.

## Installation
You will need [astral-uv](https://docs.astral.sh/uv/)

```bash
# Clone the repository
git clone git@github.com:NovaH00/clam.git
cd clam

# Install dependencies
uv sync

# Build with Nuitka
uv run build.py
```

## Usage

### Add an alias

```bash
clam add
```

Prompts for name, alias command, and description.

### Run an alias

```bash
clam run <name>
# or just run without arguments to see available aliases
clam run
```

### Show all aliases

```bash
clam show
# Show specific alias
clam show <name>
```

### Remove an alias

```bash
clam remove <name>
```

### Replace an alias

```bash
clam replace <name>
```

Shows current alias info and prompts for new values.

### Install shell completion

```bash
clam --install-completion 
```

## Configuration

Aliases are stored in `~/.config/clam/config.json`.
