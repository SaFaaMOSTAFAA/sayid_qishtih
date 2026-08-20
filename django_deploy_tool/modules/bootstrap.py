from pathlib import Path
import shutil
import subprocess

class BootstrapDeployer:
    def __init__(self, config, dry_run=False):
        self.config = config
        self.dry_run = dry_run
        self.project_path = Path(config["project_path"]).expanduser()
        self.venv_path = Path(config["venv_path"]).expanduser()
        self.media_path = Path(config["media_path"]).expanduser()
        self.requirements_path = Path(config.get("requirements_path", self.project_path / "requirements.txt")).expanduser()
        self.manage_py = Path(config.get("manage_py_path", self.project_path / "manage.py")).expanduser()
        self.python_bin = config.get("python_bin", shutil.which("python3") or "/usr/bin/python3")

    def run(self):
        if not self.manage_py.exists():
            raise FileNotFoundError(f"manage.py not found: {self.manage_py}")
        self.create_venv()
        print("[1/4] Virtual environment ready.")
        self.install_requirements()
        print("[2/4] Requirements installed.")
        self.create_media()
        print("[3/4] Media directory ready.")
        self.collectstatic()
        print("[4/4] collectstatic completed.")

    def command(self, command, cwd=None):
        print("  ->", " ".join(map(str, command)))
        if self.dry_run:
            return
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout).strip())

    def create_venv(self):
        python = self.venv_path / "bin" / "python"
        if python.exists():
            print(f"  -> Existing venv found: {self.venv_path}")
            return
        self.command([self.python_bin, "-m", "venv", str(self.venv_path)])

    def install_requirements(self):
        if not self.requirements_path.exists():
            raise FileNotFoundError(f"requirements.txt not found: {self.requirements_path}")
        pip = self.venv_path / "bin" / "pip"
        self.command([str(pip), "install", "--upgrade", "pip"])
        self.command([str(pip), "install", "-r", str(self.requirements_path)])

    def create_media(self):
        if self.media_path.exists():
            print(f"  -> Media directory exists: {self.media_path}")
            return
        if self.dry_run:
            print(f"  -> Would create: {self.media_path}")
            return
        self.media_path.mkdir(parents=True, exist_ok=True)

    def collectstatic(self):
        python = self.venv_path / "bin" / "python"
        self.command([str(python), str(self.manage_py), "collectstatic", "--noinput"], cwd=self.project_path)
