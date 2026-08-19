#!/usr/bin/env python3
"""
Django deployment bootstrap tool - Nginx module.

Usage:
    sudo python3 deploy.py --config config.yaml
    sudo python3 deploy.py --config config.yaml --dry-run

The tool:
1. Validates the configuration and important paths.
2. Renders an Nginx config from the template.
3. Installs it into sites-available.
4. Creates/updates the sites-enabled symlink.
5. Runs nginx -t.
6. Reloads Nginx only when the configuration test succeeds.
"""

import argparse
import sys
from pathlib import Path

from modules.config import load_config, validate_config
from modules.nginx import NginxDeployer


def main():
    parser = argparse.ArgumentParser(description="Django deployment tool")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without modifying the system")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        validate_config(config)

        deployer = NginxDeployer(config, dry_run=args.dry_run)
        deployer.run()

        print("\nDeployment step completed successfully.")
        return 0

    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
