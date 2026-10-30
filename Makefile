.PHONY: setup asr-model gemma run dev test

GEMMA ?= gemma4:e2b

setup:            ## Install everything except the models
	./scripts/setup.sh

asr-model:        ## Download and convert the Sunbird speech model (needs `hf auth login` first)
	.venv/bin/pip install -r scripts/requirements-convert.txt
	.venv/bin/python scripts/convert_asr.py

gemma:            ## Download Gemma 4 into Ollama
	ollama pull $(GEMMA)

run:              ## Build the web app and serve everything on http://127.0.0.1:8000
	cd frontend && npm run build
	cd backend && EBYAFAAYO_GEMMA=$(GEMMA) ../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

dev:              ## Backend with reload + Vite dev server on http://127.0.0.1:5173
	(cd backend && ../.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000) & \
	cd frontend && npm run dev

test:
	cd backend && ../.venv/bin/python -m pytest -q
