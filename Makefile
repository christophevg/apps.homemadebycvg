run:
	LOG_LEVEL=DEBUG gunicorn -k eventlet -w 1 hosted_flasks.server:app

requirements.txt:
	pip install -U pip hosted-flasks gunicorn eventlet
	pip freeze > $@

.PHONY: requirements.txt
