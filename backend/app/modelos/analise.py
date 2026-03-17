from dataclasses import dataclass, field
from typing import Any, Optional

from app.modelos.base_modelo import BaseModelo, desserializar_data


@dataclass(kw_only=True)
class Analise(BaseModelo):
    """
    Modelo local de analise persistido no arquivo JSON.
    """

    nome: str
    algoritmo: str
    tipo_algoritmo: str
    parametros: dict[str, Any] = field(default_factory=dict)
    colunas_selecionadas: list[str] = field(default_factory=list)
    status: str = "pendente"
    resultado_resumo: Optional[dict[str, Any]] = None
    caminho_resultado_csv: Optional[str] = None
    usuario_id: int = 0
    dataset_id: int = 0

    @classmethod
    def novo(
        cls,
        *,
        id: int,
        nome: str,
        algoritmo: str,
        tipo_algoritmo: str,
        parametros: Optional[dict[str, Any]],
        colunas_selecionadas: list[str],
        status: str,
        usuario_id: int,
        dataset_id: int,
    ) -> "Analise":
        """
        Cria uma nova analise com os dados de entrada necessarios para execucao.
        """
        return cls(
            id=id,
            nome=nome,
            algoritmo=algoritmo,
            tipo_algoritmo=tipo_algoritmo,
            parametros=parametros or {},
            colunas_selecionadas=colunas_selecionadas,
            status=status,
            usuario_id=usuario_id,
            dataset_id=dataset_id,
        )

    @classmethod
    def de_dict(cls, dados: dict) -> "Analise":
        """
        Reconstrui uma analise a partir do JSON persistido.
        """
        return cls(
            id=int(dados["id"]),
            nome=dados["nome"],
            algoritmo=dados["algoritmo"],
            tipo_algoritmo=dados["tipo_algoritmo"],
            parametros=dados.get("parametros") or {},
            colunas_selecionadas=list(dados.get("colunas_selecionadas") or []),
            status=dados.get("status", "pendente"),
            resultado_resumo=dados.get("resultado_resumo"),
            caminho_resultado_csv=dados.get("caminho_resultado_csv"),
            usuario_id=int(dados["usuario_id"]),
            dataset_id=int(dados["dataset_id"]),
            criado_em=desserializar_data(dados["criado_em"]),
            atualizado_em=desserializar_data(dados["atualizado_em"]),
        )
