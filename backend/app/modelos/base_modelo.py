from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def gerar_timestamp_atual() -> datetime:
    """
    Retorna o instante atual em UTC para padronizar auditoria dos registros locais.
    """
    return datetime.now(timezone.utc)


def serializar_valor(valor: Any) -> Any:
    """
    Converte valores complexos para formatos compatíveis com JSON.
    """
    if isinstance(valor, datetime):
        return valor.isoformat()
    if isinstance(valor, list):
        return [serializar_valor(item) for item in valor]
    if isinstance(valor, dict):
        return {chave: serializar_valor(item) for chave, item in valor.items()}
    return valor


def desserializar_data(valor: str) -> datetime:
    """
    Converte uma string ISO armazenada em JSON novamente para datetime.
    """
    return datetime.fromisoformat(valor)


@dataclass(kw_only=True)
class BaseModelo:
    """
    Estrutura base para os registros persistidos no banco local em JSON.
    """

    id: int
    criado_em: datetime = field(default_factory=gerar_timestamp_atual)
    atualizado_em: datetime = field(default_factory=gerar_timestamp_atual)

    def tocar(self) -> None:
        """
        Atualiza o timestamp de modificacao do registro.
        """
        self.atualizado_em = gerar_timestamp_atual()

    def para_dict(self) -> dict[str, Any]:
        """
        Serializa a instancia atual para um dicionario persistivel em JSON.
        """
        return serializar_valor(asdict(self))
