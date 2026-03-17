from dataclasses import dataclass
from typing import Any, Optional

from app.modelos.base_modelo import BaseModelo, desserializar_data


@dataclass(kw_only=True)
class Dataset(BaseModelo):
    """
    Modelo local de dataset persistido no arquivo JSON.
    """

    nome: str
    descricao: Optional[str]
    caminho_arquivo: str
    formato: str
    tamanho_bytes: int
    metadados: Optional[dict[str, Any]]
    usuario_id: int

    @classmethod
    def novo(
        cls,
        *,
        id: int,
        nome: str,
        descricao: Optional[str],
        caminho_arquivo: str,
        formato: str,
        tamanho_bytes: int,
        metadados: Optional[dict[str, Any]],
        usuario_id: int,
    ) -> "Dataset":
        """
        Cria uma nova instancia de dataset pronta para persistencia.
        """
        return cls(
            id=id,
            nome=nome,
            descricao=descricao,
            caminho_arquivo=caminho_arquivo,
            formato=formato,
            tamanho_bytes=tamanho_bytes,
            metadados=metadados,
            usuario_id=usuario_id,
        )

    @classmethod
    def de_dict(cls, dados: dict) -> "Dataset":
        """
        Reconstrui um dataset a partir do JSON persistido.
        """
        return cls(
            id=int(dados["id"]),
            nome=dados["nome"],
            descricao=dados.get("descricao"),
            caminho_arquivo=dados["caminho_arquivo"],
            formato=dados["formato"],
            tamanho_bytes=int(dados["tamanho_bytes"]),
            metadados=dados.get("metadados"),
            usuario_id=int(dados["usuario_id"]),
            criado_em=desserializar_data(dados["criado_em"]),
            atualizado_em=desserializar_data(dados["atualizado_em"]),
        )
