from platformdirs import user_config_dir
from pathlib import Path

APP_NAME = "clam"
CONFIG_DIR = Path(user_config_dir(APP_NAME))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "config.json"
CONFIG_FILE.touch()
