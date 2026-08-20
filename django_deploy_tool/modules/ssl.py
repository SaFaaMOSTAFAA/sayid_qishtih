import os
import shutil
import subprocess


class SSLDeployer:
    def __init__(self, config, dry_run=False):
        self.config = config
        self.dry_run = dry_run
        self.domain = config["domain"]
        self.email = config.get("ssl_email", "").strip()
        self.include_www = config.get("ssl_include_www", False)

    def run(self):
        if not self.dry_run and os.geteuid() != 0:
            raise PermissionError("Run SSL deployment with sudo.")

        self.check_or_install_certbot()
        print("[1/3] Certbot ready.")

        self.request_certificate()
        print("[2/3] SSL certificate requested/configured.")

        self.test_renewal()
        print("[3/3] Certificate renewal test passed.")

    def check_or_install_certbot(self):
        if shutil.which("certbot"):
            print("  -> Certbot already installed.")
            return

        print("  -> Certbot not found. Installing...")

        if shutil.which("apt-get"):
            self.command(["apt-get", "update"])
            self.command([
                "apt-get",
                "install",
                "-y",
                "certbot",
                "python3-certbot-nginx",
            ])

        elif shutil.which("dnf"):
            self.command([
                "dnf",
                "install",
                "-y",
                "certbot",
                "python3-certbot-nginx",
            ])

        elif shutil.which("yum"):
            self.command([
                "yum",
                "install",
                "-y",
                "certbot",
                "python3-certbot-nginx",
            ])

        else:
            raise RuntimeError(
                "No supported package manager found for Certbot installation."
            )

        if not self.dry_run and not shutil.which("certbot"):
            raise RuntimeError("Certbot installation failed.")

    def request_certificate(self):
        domains = ["-d", self.domain]

        if self.include_www and not self.domain.startswith("www."):
            domains.extend(["-d", f"www.{self.domain}"])

        command = [
            "certbot",
            "--nginx",
            *domains,
            "--non-interactive",
            "--agree-tos",
        ]

        if self.email:
            command.extend(["--email", self.email])
        else:
            command.append("--register-unsafely-without-email")

        command.extend([
            "--redirect",
        ])

        self.command(command)

    def test_renewal(self):
        self.command([
            "certbot",
            "renew",
            "--dry-run",
        ])

    def command(self, command):
        print("  ->", " ".join(map(str, command)))

        if self.dry_run:
            return

        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                (result.stderr or result.stdout).strip()
            )
