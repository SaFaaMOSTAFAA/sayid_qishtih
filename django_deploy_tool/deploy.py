#!/usr/bin/env python3
import argparse
import sys

from modules.config import load_config, validate_config
from modules.bootstrap import BootstrapDeployer
from modules.systemd import SystemdDeployer
from modules.nginx import NginxDeployer
from modules.ssl import SSLDeployer


def main():
    parser = argparse.ArgumentParser(description="Django Deployment Tool")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--step",
        choices=["bootstrap", "systemd", "nginx", "ssl", "all"],
        default="all",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        validate_config(config)

        if args.step in ("bootstrap", "all"):
            print("\n=== STEP 1: BOOTSTRAP ===")
            BootstrapDeployer(config, args.dry_run).run()

        if args.step in ("systemd", "all"):
            print("\n=== STEP 2: SYSTEMD / GUNICORN ===")
            SystemdDeployer(config, args.dry_run).run()

        if args.step in ("nginx", "all"):
            print("\n=== STEP 3: NGINX ===")
            NginxDeployer(config, args.dry_run).run()

        if args.step in ("ssl", "all"):
            print("\n=== STEP 4: SSL / CERTBOT ===")
            SSLDeployer(config, args.dry_run).run()

        print("\nDeployment completed successfully.")
        return 0

    except KeyboardInterrupt:
        print("\nDeployment cancelled.")
        return 130

    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
