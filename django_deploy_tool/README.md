# Django Deploy Tool

## Deployment order

### 1. Bootstrap
- Create virtual environment if missing
- Upgrade pip
- Install requirements
- Create media directory if missing
- Run `collectstatic --noinput`

### 2. Systemd / Gunicorn
- Install Gunicorn if missing
- Get workers and threads from config or interactive input
- Create systemd service
- Run `systemctl daemon-reload`
- Enable and start the service

### 3. Nginx
- Check if Nginx is installed
- Install Nginx automatically if missing
- Generate Nginx configuration
- Enable the site
- Run `nginx -t`
- Reload Nginx

### 4. SSL / Certbot
- Check if Certbot is installed
- Install Certbot and the Nginx plugin if missing
- Request a Let's Encrypt certificate
- Configure HTTP to HTTPS redirect
- Test certificate renewal

## SSL configuration

```yaml
domain: example.com
ssl_email: admin@example.com
ssl_include_www: false
```

If `ssl_include_www` is `true`, both:

- `example.com`
- `www.example.com`

will be requested.

Important: both DNS records must point to the server before requesting the certificate.

## Commands

Run everything:

    sudo python3 deploy.py --config config.yaml --step all

Run only SSL:

    sudo python3 deploy.py --config config.yaml --step ssl

Dry run:

    sudo python3 deploy.py --config config.yaml --dry-run

## Django WSGI application

Set `config_app` to the Django project package that contains `wsgi.py`:

```yaml
config_app: core
```

This deploys Gunicorn with `core.wsgi:application`. If your project uses a
non-standard WSGI target, `gunicorn_module` can still be set explicitly and
takes precedence over `config_app`.

## Viewing production logs

From the project root:

    make logs-systemd
    make logs-gunicorn
    make logs-nginx

`logs-systemd` and `logs-gunicorn` follow the `sayed_qeshta` service journal;
Gunicorn output is written there by the systemd service. `logs-nginx` follows
both Nginx access and error logs.
