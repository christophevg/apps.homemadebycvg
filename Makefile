run:
	gunicorn -k eventlet -w 1 hosted_flasks.server:app

requirements.txt:
	@cat $@ | cut -d"=" -f1 | xargs pip uninstall -y
	pip install -U pip
	pip install -r requirements.base.txt
	pip freeze > $@

.PHONY: requirements.txt

add:
	git submodule add $(REPO)

init:
	git submodule update --init --recursive

update: pullall requirements.txt

pullall:
	git submodule foreach git pull origin master
