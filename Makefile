PYTHON = venv/bin/python3
MANAGE = $(PYTHON) manage.py
SERVICE = sayed_qeshta

.PHONY: run migrate makemigrations makemessages compilemessages shell superuser logs-systemd logs-gunicorn logs-nginx

run:
	$(MANAGE) runserver

migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations

makemessages:
	$(MANAGE) makemessages -l ar --ignore=venv/*

compilemessages:
	$(MANAGE) compilemessages --ignore=venv/*

shell:
	$(MANAGE) shell

superuser:
	$(MANAGE) createsuperuser

# Follow the application service journal (Gunicorn writes its stdout/stderr here).
logs-systemd:
	sudo journalctl -u $(SERVICE).service -f -n 100

# Gunicorn stdout/stderr is captured by the same systemd service journal.
logs-gunicorn:
	sudo journalctl -u $(SERVICE).service -f -n 100

logs-nginx:
	sudo tail -F /var/log/nginx/access.log /var/log/nginx/error.log
