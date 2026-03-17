from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class AnaliseBase(BaseModel):
    """
    Campos comuns para a análise.
    """
    nome: str = Field(..., min_length=3, max_length=150, description="Nome identificador da análise")
    algoritmo: str = Field(..., description="Identificador do algoritmo (ex: isolation_forest, zscore)")
    tipo_algoritmo: str = Field(..., description="Categoria do algoritmo (estatistico, machine_learning, temporal)")

class AnaliseCriar(AnaliseBase):
    """
    Esquema para criação de uma nova análise.
    Exige o ID do dataset e as colunas selecionadas.
    """
    dataset_id: int = Field(..., description="ID do dataset a ser analisado")
    colunas_selecionadas: List[str] = Field(..., min_length=1, description="Lista de colunas numéricas para análise")
    parametros: Optional[Dict[str, Any]] = Field(default={}, description="Parâmetros específicos do algoritmo")

class AnaliseResposta(AnaliseBase):
    """
    Esquema para resposta da API.
    Inclui o status, resumo dos resultados e caminhos de arquivos.
    """
    id: int
    dataset_id: int
    colunas_selecionadas: List[str]
    parametros: Optional[Dict[str, Any]]
    status: str
    resultado_resumo: Optional[Dict[str, Any]] = None
    caminho_resultado_csv: Optional[str] = None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)

class ResultadoAnomalia(BaseModel):
    """
    Esquema para um registro anômalo individual.
    """
    indice_original: int
    score: float
    justificativa: str
    dados_registro: Dict[str, Any]
