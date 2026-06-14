PYTHON = venv/bin/python3
MANAGE = $(PYTHON) manage.py

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

