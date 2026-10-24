PYTHON ?= python
NPM ?= npm

.PHONY: help install install-backend install-frontend dev backend frontend test test-frontend benchmark amenities build clean

help:
	@echo SG Property Finder
	@echo   make install          - install backend and frontend dependencies
	@echo   make install-backend  - install backend Python dependencies
	@echo   make install-frontend - install frontend Node dependencies
	@echo   make dev              - run FastAPI and Vite together (Ctrl+C stops both)
	@echo   make backend          - run only FastAPI on port 8000
	@echo   make frontend         - run only Vite on port 5173
	@echo   make test             - run backend unittest suite
	@echo   make test-frontend    - run frontend Vitest suite
	@echo   make benchmark        - run the Phase 5 SLA benchmark
	@echo   make amenities        - rebuild backend/assets/data/amenities.json
	@echo   make build            - type-check and build the frontend
	@echo   make clean            - remove frontend dist and Python caches

install: install-backend install-frontend

install-backend:
	$(PYTHON) -m pip install -r backend/requirements.txt

install-frontend:
	$(NPM) --prefix frontend install --no-audit --no-fund

dev:
	$(PYTHON) scripts/dev.py

backend:
	$(PYTHON) scripts/dev.py --backend-only

frontend:
	$(PYTHON) scripts/dev.py --frontend-only

test:
	$(PYTHON) scripts/test_backend.py

test-frontend:
	$(NPM) --prefix frontend test

benchmark:
	$(PYTHON) scripts/benchmark_api.py --spawn-server --warm-samples 50

amenities:
	$(PYTHON) scripts/build_amenities.py

build:
	$(NPM) --prefix frontend run build

clean:
	$(PYTHON) scripts/clean.py
