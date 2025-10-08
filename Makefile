# Load environment variables from dev.env file
include secrets/dev.env
export

.EXPORT_ALL_VARIABLES:

venv:
	python3 -m venv venv

run:
	source venv/bin/activate && python3 main.py

requirements:
	source venv/bin/activate && pip install -r requirements.txt

freeze:
	source venv/bin/activate && pip freeze

build:
	docker build -t abb .

.PHONY: example
example:
	cd example && ./start.sh
