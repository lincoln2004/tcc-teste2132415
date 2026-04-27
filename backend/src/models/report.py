from pydantic import BaseModel, Field
from typing import Any

class ReportRequest(BaseModel):
    selecionados: list[str]
    colunas_numericas: list[str]
    colunas_categoricas: list[str]
    threshold: float = Field(default=0.05, ge=0.01, le=0.5)

class ReportResponse(BaseModel):
    arquivo: dict[str, Any]
    analise_geral: dict[str, Any]
    estatisticas: dict[str, Any]
    modelos: dict[str, Any]
