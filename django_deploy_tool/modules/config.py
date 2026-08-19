from pathlib import Path
import yaml


REQUIRED_KEYS = [
    "project_name",
    "domain",
    "project_path",
    "venv_path",
    "static_path",
    "media_path",
]


def load_config(path):
    config_path = Path(path).expanduser().resolve()

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    return config


def validate_config(config):
    missing = [key for key in REQUIRED_KEYS if not config.get(key)]
    if missing:
        raise ValueError(
            "Missing required config values: " + ", ".join(missing)
        )

    project_path = Path(config["project_path"]).expanduser()

    if not project_path.exists():
        raise ValueError(f"Project path does not exist: {project_path}")

    for key in ("static_path", "media_path", "venv_path"):
        value = Path(config[key]).expanduser()
        if not value.exists():
            raise ValueError(f"{key} does not exist: {value}")
