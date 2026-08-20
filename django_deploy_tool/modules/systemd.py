from pathlib import Path
import os
import subprocess

class SystemdDeployer:
    def __init__(self, config, dry_run=False):
        self.config = config
        self.dry_run = dry_run
        self.project_name = config["project_name"]
        self.project_path = Path(config["project_path"]).expanduser()
        self.venv_path = Path(config["venv_path"]).expanduser()
        self.port = int(config["port"])
        self.gunicorn_module = config["gunicorn_module"]
        self.user = config.get("service_user", "www-data")
        self.group = config.get("service_group", self.user)
        self.workers = self.get_number("workers", 3)
        self.threads = self.get_number("threads", 2)
        self.service_path = Path(config.get(
            "systemd_path",
            f"/etc/systemd/system/{self.project_name}.service"
        ))

    def get_number(self, name, default):
        value = self.config.get(name)

        if value not in (None, ""):
            try:
                value = int(value)
                if value < 1:
                    raise ValueError
                print(f"  -> Using {name} from config: {value}")
                return value
            except (TypeError, ValueError):
                raise ValueError(f"{name} must be a positive integer")

        while True:
            raw = input(f"Enter number of Gunicorn {name} [{default}]: ").strip()
            if not raw:
                return default
            try:
                value = int(raw)
                if value < 1:
                    raise ValueError
                return value
            except ValueError:
                print("Please enter a positive integer.")

    def run(self):
        if not self.dry_run and os.geteuid() != 0:
            raise PermissionError("Run systemd deployment with sudo.")

        self.ensure_gunicorn()
        print("[1/5] Gunicorn ready.")

        content = self.render_service()
        print("[2/5] Systemd service generated.")

        self.write_service(content)
        print(f"[3/5] Service installed: {self.service_path}")

        self.command(["systemctl", "daemon-reload"])
        print("[4/5] systemd daemon reloaded.")

        self.command(["systemctl", "enable", "--now", f"{self.project_name}.service"])
        print("[5/5] Gunicorn service enabled and started.")

    def ensure_gunicorn(self):
        gunicorn = self.venv_path / "bin" / "gunicorn"
        if gunicorn.exists():
            return
        pip = self.venv_path / "bin" / "pip"
        self.command([str(pip), "install", "gunicorn"])

    def render_service(self):
        gunicorn = self.venv_path / "bin" / "gunicorn"
        return f"""[Unit]
Description=Gunicorn service for {self.project_name}
After=network.target

[Service]
User={self.user}
Group={self.group}
WorkingDirectory={self.project_path}
Environment="PATH={self.venv_path}/bin"

ExecStart={gunicorn} --workers {self.workers} --threads {self.threads} --bind 127.0.0.1:{self.port} {self.gunicorn_module}

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

    def write_service(self, content):
        if self.dry_run:
            print("\n--- DRY RUN: SYSTEMD SERVICE ---")
            print(content)
            print("--- END ---\n")
            return
        self.service_path.parent.mkdir(parents=True, exist_ok=True)
        self.service_path.write_text(content, encoding="utf-8")
        self.service_path.chmod(0o644)

    def command(self, command):
        print("  ->", " ".join(map(str, command)))
        if self.dry_run:
            return
        result = subprocess.run(command, text=True, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout).strip())
