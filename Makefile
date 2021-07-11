.PHONY: default
default: build

build: venv

venv:
	python3 -m venv .venv

reqs:
	pip install -r requirements.txt

run:
	python3 main.py

freeze:
	pip freeze > requirements.txt

# clean up
.PHONY: clean
clean:
	rm -rf .venv
