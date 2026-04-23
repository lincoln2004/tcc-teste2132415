from pydantic import BaseModel
from typing import Any

class ReportRequest(BaseModel):
    selecionados: list[str]
    colunas_numericas: list[str]
    colunas_categoricas: list[str]

class ReportResponse(BaseModel):
    arquivo: dict[str, Any]
    analise_geral: dict[str, Any]
    estatisticas: dict[str, Any]
    modelos: dict[str, Any]
