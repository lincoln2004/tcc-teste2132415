import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.rotas import analises_rota, auth_rota, datasets_rota
from app.banco.banco_json import banco_json
from app.configuracoes.configuracoes import configuracoes
from app.logs.config_log import logger


@asynccontextmanager
async def ciclo_vida(_app: FastAPI):
    """
    Prepara a estrutura local da aplicacao antes de aceitar requisicoes.
    """
    os.makedirs(configuracoes.UPLOAD_DIR, exist_ok=True)
    await banco_json.inicializar()
    logger.info("Persistencia local em JSON pronta para uso.")

    yield


def criar_aplicacao() -> FastAPI:
    """
    Fabrica a aplicacao FastAPI com rotas, CORS e persistencia local em JSON.
    """
    app = FastAPI(
        title=configuracoes.PROJECT_NAME,
        openapi_url=f"{configuracoes.API_V1_STR}/openapi.json",
        description="API para Plataforma de Deteccao de Anomalias em Dados Multissetoriais",
        lifespan=ciclo_vida,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origem) for origem in configuracoes.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_rota.router, prefix=f"{configuracoes.API_V1_STR}/auth", tags=["Autenticacao"])
    app.include_router(datasets_rota.router, prefix=f"{configuracoes.API_V1_STR}/datasets", tags=["Datasets"])
    app.include_router(analises_rota.router, prefix=f"{configuracoes.API_V1_STR}/analises", tags=["Analises"])

    @app.get("/")
    async def root() -> dict[str, str]:
        """
        Endpoint de saude da API.
        """
        return {
            "projeto": configuracoes.PROJECT_NAME,
            "versao": "1.1.1",
            "status": "online",
            "persistencia": "json_local",
        }

    logger.info("Aplicacao FastAPI inicializada com sucesso.")
    return app


app = criar_aplicacao()
