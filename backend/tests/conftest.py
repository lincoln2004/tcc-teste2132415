import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

RAIZ_BACKEND = Path(__file__).resolve().parents[1]

if str(RAIZ_BACKEND) not in sys.path:
    sys.path.insert(0, str(RAIZ_BACKEND))

from app.configuracoes.configuracoes import configuracoes
from app.main import app
from app.seguranca.limitador_requisicoes import limitador_auth


@pytest.fixture
def cliente(tmp_path: Path):
    """
    Configura um ambiente isolado de teste usando banco local em JSON temporario.
    """
    banco_original = configuracoes.BANCO_JSON_PATH
    upload_original = configuracoes.UPLOAD_DIR

    configuracoes.BANCO_JSON_PATH = str(tmp_path / "banco_teste.json")
    configuracoes.UPLOAD_DIR = str(tmp_path / "uploads")
    limitador_auth.resetar()

    with TestClient(app) as client:
        yield client

    limitador_auth.resetar()
    configuracoes.BANCO_JSON_PATH = banco_original
    configuracoes.UPLOAD_DIR = upload_original
