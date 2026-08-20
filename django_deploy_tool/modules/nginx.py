from pathlib import Path
import os
import shutil
import subprocess

class NginxDeployer:
    def __init__(self, config, dry_run=False):
        self.config = config
        self.dry_run = dry_run
        self.project_name = config["project_name"]
        self.port = int(config["port"])
        self.template_path = Path(__file__).resolve().parent.parent / "templates" / "nginx.conf.j2"
        self.available = Path(config.get("nginx_sites_available", "/etc/nginx/sites-available"))
        self.enabled = Path(config.get("nginx_sites_enabled", "/etc/nginx/sites-enabled"))
        self.target = self.available / self.project_name
        self.link = self.enabled / self.project_name

    def run(self):
        if not self.dry_run and os.geteuid() != 0:
            raise PermissionError("Run Nginx deployment with sudo.")
        self.check_or_install_nginx()
        print("[1/5] Nginx ready.")
        content = self.render_config()
        print("[2/5] Nginx configuration generated.")
        self.install_config(content)
        print("[3/5] Nginx configuration installed.")
        self.enable_site()
        print("[4/5] Site enabled.")
        self.command(["nginx", "-t"])
        self.command(["systemctl", "reload", "nginx"])
        print("[5/5] Nginx tested and reloaded.")

    def check_or_install_nginx(self):
        if shutil.which("nginx"):
            print("  -> Nginx already installed.")
            return
        print("  -> Nginx not found. Installing...")
        if shutil.which("apt-get"):
            self.command(["apt-get", "update"])
            self.command(["apt-get", "install", "-y", "nginx"])
        elif shutil.which("dnf"):
            self.command(["dnf", "install", "-y", "nginx"])
        elif shutil.which("yum"):
            self.command(["yum", "install", "-y", "nginx"])
        else:
            raise RuntimeError("No supported package manager found.")
        if not self.dry_run and not shutil.which("nginx"):
            raise RuntimeError("Nginx installation failed.")
        self.command(["systemctl", "enable", "--now", "nginx"])

    def render_config(self):
        content = self.template_path.read_text(encoding="utf-8")
        values = {
            "domain": self.config["domain"],
            "static_path": self.config["static_path"],
            "media_path": self.config["media_path"],
            "port": self.port,
        }
        for key, value in values.items():
            content = content.replace("{{ " + key + " }}", str(value))
        return content

    def install_config(self, content):
        if self.dry_run:
            print("\n--- DRY RUN: NGINX CONFIG ---")
            print(content)
            print("--- END ---\n")
            return
        self.available.mkdir(parents=True, exist_ok=True)
        self.target.write_text(content, encoding="utf-8")

    def enable_site(self):
        if self.dry_run:
            return
        self.enabled.mkdir(parents=True, exist_ok=True)
        if self.link.exists() or self.link.is_symlink():
            self.link.unlink()
        self.link.symlink_to(self.target)

    def command(self, command):
        print("  ->", " ".join(map(str, command)))
        if self.dry_run:
            return
        result = subprocess.run(command, text=True, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout).strip())
