JACKETT_API_KEY:=$(shell cat secrets/jackett.json | jq -r '.JACKETT_API_KEY')
JACKETT_API_URL:=$(shell cat secrets/jackett.json | jq -r '.JACKETT_API_URL')
TRANSMISSION_URL:=$(shell cat secrets/transmission.json | jq -r '.TRANSMISSION_URL')
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
