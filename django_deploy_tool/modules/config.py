from pathlib import Path
import yaml

REQUIRED_KEYS = [
    "project_name", "domain", "project_path", "venv_path",
    "static_path", "media_path", "port"
]

def load_config(path):
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open(encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    # An explicit module supports non-standard WSGI layouts.  Otherwise derive
    # the conventional target from config_app (core by default).
    if not config.get("gunicorn_module"):
        config_app = config.get("config_app", "core")
        if not isinstance(config_app, str) or not config_app.strip():
            raise ValueError("config_app must be a non-empty Django package name")
        config["gunicorn_module"] = f"{config_app.strip()}.wsgi:application"

    return config

def validate_config(config):
    missing = [k for k in REQUIRED_KEYS if config.get(k) in (None, "")]
    if missing:
        raise ValueError("Missing required config values: " + ", ".join(missing))

    if not Path(config["project_path"]).expanduser().exists():
        raise ValueError(f"Project path does not exist: {config['project_path']}")

    try:
        port = int(config["port"])
    except (TypeError, ValueError):
        raise ValueError("port must be a number")

    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
