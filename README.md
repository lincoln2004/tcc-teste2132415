# Plataforma de Deteccao de Anomalias

Projeto full-stack com frontend React, backend FastAPI e persistencia local em JSON.

## Execucao local

### Frontend + backend integrado

1. Instale as dependencias do frontend:
   `npm install`
2. Crie o arquivo `.env` na raiz com base em `.env.example`.
3. Crie um ambiente virtual Python e instale as dependencias do backend:
   `python -m venv .venv`
   `.\.venv\Scripts\python -m pip install -r requirements.txt`
4. Crie o arquivo `backend/.env` com base em `backend/.env.example`.
5. Inicie a aplicacao integrada:
   `npm run dev`

### Backend isolado

1. Ative o ambiente virtual Python:
   `.\.venv\Scripts\activate`
2. Acesse a pasta do backend:
   `cd backend`
3. Inicie a API:
   `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

## Banco local em JSON

- Arquivo padrao:
  `backend/dados/banco_local.json`
- Uploads:
  `backend/uploads`
- Para mudar o caminho do banco, ajuste:
  `BANCO_JSON_PATH` no `backend/.env`

## Testes automatizados

1. Ative o ambiente virtual:
   `.\.venv\Scripts\activate`
2. Execute os testes do backend:
   `python -m pytest backend/tests -q`

## Docker Compose

1. Suba os servicos:
   `docker compose up --build`
2. Frontend:
   `http://localhost:3000`
3. Backend:
   `http://localhost:8000`
4. Swagger:
   `http://localhost:8000/docs`
