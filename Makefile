DASHBOARD_APP ?= app/frontend/dashboard.py

run:
	streamlit run ${DASHBOARD_APP}

categorize:
	python -m app.cli categorize --file ${FILE} --out ${OUT:-output} --out_filename ${OUT_FILENAME:-Hasil_Analisis_Proyek_Penelitian_V5_0} --dataset_type ${DATASET_TYPE:-research}

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

keyword-add-group:
	python -m app.cli keyword add-group --order ${ORDER} --label "${LABEL}"

keyword-add-efficiency:
	python -m app.cli keyword add-efficiency --order ${ORDER} --keyword "${KEYWORD}"

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

.PHONY: run categorize init-db sanitize-db seed-config keyword-list keyword-add-cue keyword-add-group keyword-add-efficiency keyword-remove-efficiency keyword-set-threshold podman-build podman-run podman-stop

