from pathlib import Path
import os
import subprocess


class NginxDeployer:
    def __init__(self, config, dry_run=False):
        self.config = config
        self.dry_run = dry_run

        self.template_path = (
            Path(__file__).resolve().parent.parent
            / "templates"
            / "nginx.conf.j2"
        )

        self.nginx_available = Path(
            config.get("nginx_sites_available", "/etc/nginx/sites-available")
        )
        self.nginx_enabled = Path(
            config.get("nginx_sites_enabled", "/etc/nginx/sites-enabled")
        )

        self.site_name = config["project_name"]
        self.target_path = self.nginx_available / self.site_name
        self.link_path = self.nginx_enabled / self.site_name

    def run(self):
        self._check_root()
        self._check_template()
        rendered = self._render_template()

        print("[1/5] Nginx configuration generated.")

        self._install_config(rendered)
        print(f"[2/5] Installed: {self.target_path}")

        self._enable_site()
        print(f"[3/5] Enabled site: {self.link_path}")

        self._nginx_test()
        print("[4/5] nginx -t passed.")

        self._reload_nginx()
        print("[5/5] Nginx reloaded.")

    def _check_root(self):
        if self.dry_run:
            return

        if os.geteuid() != 0:
            raise PermissionError(
                "This operation needs root privileges. Run with sudo."
            )

    def _check_template(self):
        if not self.template_path.exists():
            raise FileNotFoundError(
                f"Nginx template not found: {self.template_path}"
            )

    def _render_template(self):
        template = self.template_path.read_text(encoding="utf-8")

        values = {
            "domain": self.config["domain"],
            "project_path": self.config["project_path"],
            "venv_path": self.config["venv_path"],
            "static_path": self.config["static_path"],
            "media_path": self.config["media_path"],
            "upstream_socket": self.config.get(
                "upstream_socket",
                f"/run/{self.config['project_name']}.sock",
            ),
        }

        for key, value in values.items():
            template = template.replace("{{ " + key + " }}", str(value))

        return template

    def _install_config(self, content):
        if self.dry_run:
            print("\n--- DRY RUN: Nginx config ---")
            print(content)
            print("--- END DRY RUN ---\n")
            return

        self.nginx_available.mkdir(parents=True, exist_ok=True)
        self.nginx_enabled.mkdir(parents=True, exist_ok=True)

        self.target_path.write_text(content, encoding="utf-8")
        self.target_path.chmod(0o644)

    def _enable_site(self):
        if self.dry_run:
            return

        if self.link_path.is_symlink() or self.link_path.exists():
            if self.link_path.is_symlink():
                if self.link_path.resolve() == self.target_path.resolve():
                    return
            self.link_path.unlink()

        self.link_path.symlink_to(self.target_path)

    def _nginx_test(self):
        if self.dry_run:
            print("[DRY RUN] Would execute: nginx -t")
            return

        self._run(["nginx", "-t"])

    def _reload_nginx(self):
        if self.dry_run:
            print("[DRY RUN] Would execute: systemctl reload nginx")
            return

        self._run(["systemctl", "reload", "nginx"])

    @staticmethod
    def _run(command):
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            details = (result.stderr or result.stdout).strip()
            raise RuntimeError(
                f"Command failed: {' '.join(command)}\n{details}"
            )
