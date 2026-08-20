# Django Deploy Tool

## Deployment order

1. Bootstrap
   - Create venv if missing
   - Upgrade pip
   - Install requirements
   - Create media directory
   - Run collectstatic

2. Systemd / Gunicorn
   - Install Gunicorn if missing
   - Get workers and threads
   - Create systemd service
   - daemon-reload
   - enable and start service

3. Nginx
   - Check/install Nginx
   - Create Nginx config
   - Enable site
   - nginx -t
   - Reload Nginx

## Workers and threads

You can define them in config.yaml:

    workers: 4
    threads: 2

Or remove them from config.yaml and the script asks:

    Enter number of Gunicorn workers [3]:
    Enter number of Gunicorn threads [2]:

Press Enter to use the defaults.

## Run

    sudo python3 deploy.py --config config.yaml --step all

Dry run:

    sudo python3 deploy.py --config config.yaml --dry-run
