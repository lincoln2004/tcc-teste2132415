PYTHON = backend/.venv/Scripts/python
PIP    = backend/.venv/Scripts/pip

.PHONY: dev install install-backend install-frontend setup backend frontend

dev: install setup
	@echo ">>> Subindo backend e frontend..."
	@$(MAKE) -j2 backend frontend

install: install-backend install-frontend

install-backend:
	@echo ">>> Instalando dependências Python..."
	@if [ ! -d backend/.venv ]; then cd backend && python -m venv .venv; fi
	$(PIP) install -r backend/requirements.txt

install-frontend:
	@echo ">>> Instalando dependências Node..."
	cd frontend && npm install

setup:
	$(PYTHON) backend/setup_supabase.py

backend:
	cd backend && $(CURDIR)/$(PYTHON) -m uvicorn src.main:app --reload

frontend:
	cd frontend && npm run dev
