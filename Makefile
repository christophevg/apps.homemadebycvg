run:
	source .env.local; env; LOG_LEVEL=DEBUG gunicorn -k eventlet -w 1 hosted_flasks.server:app

requirements.txt:
	pip install -U pip hosted-flasks gunicorn eventlet
	pip freeze > $@

.PHONY: requirements.txt

add:
	git submodule add $(REPO)

init:
	git submodule update --init --recursive

update:
	git submodule foreach git pull origin master
