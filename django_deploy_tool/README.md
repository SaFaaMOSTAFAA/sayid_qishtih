# Django Deploy Tool

This is the first module of the deployment tool: Nginx.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure

```bash
cp config.yaml.example config.yaml
nano config.yaml
```

Set:

- `project_name`
- `domain`
- `project_path`
- `venv_path`
- `static_path`
- `media_path`

## Test safely

```bash
sudo .venv/bin/python deploy.py --config config.yaml --dry-run
```

## Deploy Nginx

```bash
sudo .venv/bin/python deploy.py --config config.yaml
```

The module will:

1. Validate the config.
2. Render the Nginx template.
3. Write `sites-available/<project_name>`.
4. Create the `sites-enabled/<project_name>` symlink.
5. Run `nginx -t`.
6. Reload Nginx only after a successful test.

The next modules can be added independently for Gunicorn/systemd, SSL, project bootstrap, migrations, collectstatic, health checks, and rollback.
