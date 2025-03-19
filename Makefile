JACKETT_API_KEY:=$(shell cat secrets/jackett.json | jq -r '.JACKETT_API_KEY')
JACKETT_API_URL:=$(shell cat secrets/jackett.json | jq -r '.JACKETT_API_URL')
TRANSMISSION_URL:=$(shell cat secrets/transmission.json | jq -r '.TRANSMISSION_URL')
TRANSMISSION_USER:=$(shell cat secrets/transmission.json | jq -r '.TRANSMISSION_USER')
TRANSMISSION_PASS:=$(shell cat secrets/transmission.json | jq -r '.TRANSMISSION_PASS')
BEETS_INPUT_PATH:=$(shell cat secrets/beets.json | jq -r '.BEETS_INPUT_PATH')
BEETS_OUTPUT_PATH:=$(shell cat secrets/beets.json | jq -r '.BEETS_OUTPUT_PATH')
BEETSDIR:=$(shell cat secrets/beets.json | jq -r '.BEETSDIR')
ADMIN_ID:=$(shell od -x /dev/urandom | head -1 | awk '{OFS="-"; print $$2$$3,$$4,$$5,$$6,$$7$$8$$9}')
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
