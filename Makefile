DASHBOARD_APP ?= app/ui/dashboard/main.py
OUT ?= output
OUT_FILENAME ?= community_service_result
DATASET_TYPE ?= community_service

run:
	PYTHONPATH=$(shell pwd) streamlit run ${DASHBOARD_APP}

api-run:
	PYTHONPATH=$(shell pwd) uvicorn app.api.main:app --reload

init-db:
	python -m app.cli init-db

sanitize-db:
	python -m app.cli sanitize-db

seed-config:
	python -m app.cli seed-config

keyword-list:
	python -m app.cli keyword list

keyword-add-cue:
	python -m app.cli keyword add-cue "${WORD}"

keyword-remove-efficiency:
	python -m app.cli keyword remove-efficiency --id ${ID}

keyword-set-threshold:
	python -m app.cli keyword set-threshold --key ${KEY} --value ${VALUE}

podman-build:
	podman build -t entropy-app -f Containerfile .

podman-run:
	podman run -d -p 8501:8501 --name entropy-dashboard -v $(shell pwd)/entropy.db:/app/entropy.db:U entropy-app

podman-stop:
	podman stop entropy-dashboard || true
	podman rm entropy-dashboard || true

.PHONY: run api-run init-db sanitize-db seed-config keyword-list keyword-add-cue keyword-remove-efficiency keyword-set-threshold podman-build podman-run podman-stop

