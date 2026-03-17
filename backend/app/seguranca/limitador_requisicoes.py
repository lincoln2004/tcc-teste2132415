from collections import defaultdict
from datetime import datetime, timedelta, timezone


class LimitadorRequisicoes:
    """
    Mantem um controle simples em memoria das tentativas recentes por chave.
    """

    def __init__(self) -> None:
        self._tentativas: dict[str, list[datetime]] = defaultdict(list)

    def registrar_tentativa(self, chave: str, limite: int, janela_segundos: int) -> None:
        """
        Registra uma tentativa e sinaliza quando o limite da janela foi excedido.
        """
        agora = datetime.now(timezone.utc)
        inicio_janela = agora - timedelta(seconds=janela_segundos)
        tentativas_validas = [item for item in self._tentativas[chave] if item >= inicio_janela]
        if len(tentativas_validas) >= limite:
            raise ValueError("Muitas tentativas recentes. Aguarde alguns minutos e tente novamente.")
        tentativas_validas.append(agora)
        self._tentativas[chave] = tentativas_validas

    def limpar_tentativas(self, chave: str) -> None:
        """
        Remove o historico de uma chave apos uma autenticacao bem-sucedida.
        """
        self._tentativas.pop(chave, None)

    def resetar(self) -> None:
        """
        Limpa todo o estado em memoria, util em testes automatizados.
        """
        self._tentativas.clear()


limitador_auth = LimitadorRequisicoes()
