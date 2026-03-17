from pathlib import Path
from typing import List, Union

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


CAMINHO_ENV_BACKEND = Path(__file__).resolve().parents[2] / ".env"


class Configuracoes(BaseSettings):
    """
    Classe de configuracoes da aplicacao.
    Centraliza os parametros de ambiente usados pelo backend local.
    """

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "SUA_CHAVE_SECRETA_PADRAO_NAO_USE_EM_PRODUCAO"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    PROJECT_NAME: str = "Plataforma de Deteccao de Anomalias"

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    BANCO_JSON_PATH: str = "./dados/banco_local.json"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024

    JANELA_TENTATIVAS_AUTH_SEGUNDOS: int = 300
    LIMITE_TENTATIVAS_LOGIN: int = 10
    LIMITE_TENTATIVAS_CADASTRO: int = 5

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, valor: Union[str, List[str]]) -> Union[List[str], str]:
        """
        Converte a configuracao de CORS para uma lista valida de origens.
        """
        if isinstance(valor, str) and not valor.startswith("["):
            return [origem.strip() for origem in valor.split(",")]
        if isinstance(valor, (list, str)):
            return valor
        raise ValueError(valor)

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=str(CAMINHO_ENV_BACKEND),
        extra="ignore",
    )


configuracoes = Configuracoes()
