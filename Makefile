JACKETT_API_KEY:=$(shell cat secrets/jackett.json | jq -r '.JACKETT_API_KEY')
JACKETT_API_URL:=$(shell cat secrets/jackett.json | jq -r '.JACKETT_API_URL')
TRANSMISSION_URL:=$(shell cat secrets/transmission.json | jq -r '.TRANSMISSION_URL')
TRANSMISSION_USER:=$(shell cat secrets/transmission.json | jq -r '.TRANSMISSION_USER')
TRANSMISSION_PASS:=$(shell cat secrets/transmission.json | jq -r '.TRANSMISSION_PASS')
BEETS_INPUT_PATH:=$(shell cat secrets/beets.json | jq -r '.BEETS_INPUT_PATH')
BEETSDIR:=$(shell cat secrets/beets.json | jq -r '.BEETSDIR')
USE_BEETS_IMPORT:=$(shell cat secrets/beets.json | jq -r '.USE_BEETS_IMPORT')
ADMIN_ID:=dummy
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
