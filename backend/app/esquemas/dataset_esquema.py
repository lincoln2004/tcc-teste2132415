from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class DatasetBase(BaseModel):
    """
    Campos comuns para o dataset.
    """
    nome: str = Field(..., min_length=3, max_length=150, description="Nome identificador do dataset")
    descricao: Optional[str] = Field(None, max_length=500, description="Breve descrição do conteúdo")

class DatasetCriar(DatasetBase):
    """
    Esquema para criação de um novo dataset.
    Os campos de arquivo e tamanho são preenchidos automaticamente pelo serviço.
    """
    pass

class DatasetAtualizar(BaseModel):
    """
    Esquema para atualização de metadados do dataset.
    """
    nome: Optional[str] = None
    descricao: Optional[str] = None

class DatasetResposta(DatasetBase):
    """
    Esquema para resposta da API.
    Inclui metadados extraídos e informações do arquivo físico.
    """
    id: int
    formato: str
    tamanho_bytes: int
    metadados: Optional[Dict[str, Any]] = None
    usuario_id: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)

class MetadadosColuna(BaseModel):
    """
    Esquema para os metadados de uma coluna específica.
    """
    nome: str
    tipo: str
    estatisticas: Dict[str, Any]
    valores_nulos: int
    percentual_nulos: float
