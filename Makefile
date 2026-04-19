# Detecta o sistema operacional e define os caminhos corretos do venv
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    VENV_BIN   := $(VENV_DIR)/bin
else ifeq ($(UNAME_S),Darwin)
    VENV_BIN   := $(VENV_DIR)/bin
else
    # Assume Windows (Cygwin/MSYS2 ou cmd.exe com make)
    VENV_BIN   := $(VENV_DIR)/Scripts
endif

PYTHON   := python3
VENV_DIR := .venv
VENV_PY  := $(VENV_BIN)/python
PIP      := $(VENV_BIN)/pip
PYTEST   := $(VENV_BIN)/pytest

.PHONY: help install install-frontend install-backend setup dev dev-backend dev-frontend test clean

help:
	@echo "Comandos disponíveis:"
	@echo "  make setup            Cria arquivos .env a partir dos exemplos"
	@echo "  make install          Instala todas as dependências (frontend + backend)"
	@echo "  make install-frontend Instala dependências do frontend"
	@echo "  make install-backend  Cria venv e instala dependências do backend"
	@echo "  make dev              Inicia frontend + backend integrado"
	@echo "  make dev-frontend     Inicia apenas o frontend (sem backend)"
	@echo "  make dev-backend      Inicia apenas o backend (FastAPI)"
	@echo "  make test             Executa os testes do backend"
	@echo "  make clean            Remove artefatos de build"

# ── Configuração inicial ────────────────────────────────────────────────────

setup:
	@if [ ! -f .env ]; then cp .env.example .env && echo "Criado .env na raiz"; else echo ".env já existe"; fi
	@if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env && echo "Criado backend/.env"; else echo "backend/.env já existe"; fi

# ── Instalação ──────────────────────────────────────────────────────────────

install: install-frontend install-backend

install-frontend: node_modules/.install.stamp

node_modules/.install.stamp: package.json
	npm install
	@touch $@

install-backend: $(VENV_DIR)/.install.stamp

$(VENV_DIR)/.install.stamp: requirements.txt
	@if [ ! -d "$(VENV_DIR)" ] || ! $(VENV_PY) --version > /dev/null 2>&1; then \
		echo "Criando/recriando ambiente virtual em $(VENV_DIR)..."; \
		rm -rf $(VENV_DIR); \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi
	$(VENV_PY) -m pip install --upgrade pip --quiet
	$(VENV_PY) -m pip install -r requirements.txt
	@touch $@

# ── Execução ────────────────────────────────────────────────────────────────

# Instala deps (se necessário) e inicia o Express + backend Python via server.ts
dev: install
	npm run dev

# Apenas o frontend/Express (sem subir o backend Python)
dev-frontend:
	INICIAR_BACKEND_INTEGRADO=false npm run dev

# Apenas o backend FastAPI (com reload automático)
dev-backend:
	cd backend && ../$(VENV_PY) -m uvicorn app.main:app \
		--host 127.0.0.1 \
		--port 8000 \
		--reload

# ── Testes ──────────────────────────────────────────────────────────────────

test:
	cd backend && ../$(PYTEST) tests -v

# ── Limpeza ─────────────────────────────────────────────────────────────────

clean:
	npm run clean
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -name "*.pyc" -delete 2>/dev/null || true
