import asyncio
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Optional

from loguru import logger

from app.configuracoes.configuracoes import configuracoes


class BancoJsonLocal:
    """
    Gerencia a persistencia local da aplicacao em um unico arquivo JSON.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    def obter_caminho_arquivo(self) -> Path:
        """
        Resolve o caminho absoluto do arquivo JSON usado como banco local.
        """
        caminho_configurado = os.getenv("BANCO_JSON_PATH", configuracoes.BANCO_JSON_PATH)
        caminho = Path(caminho_configurado)
        if not caminho.is_absolute():
            caminho = Path.cwd() / caminho
        return caminho

    def obter_dados_iniciais(self) -> dict[str, Any]:
        """
        Retorna a estrutura minima esperada pelo banco local.
        """
        return {
            "usuarios": [],
            "datasets": [],
            "analises": [],
            "sequencias": {
                "usuarios": 0,
                "datasets": 0,
                "analises": 0,
            },
        }

    def _ler_dados_sem_lock(self) -> dict[str, Any]:
        """
        Le o arquivo JSON ja assumindo que o acesso esta serializado por lock.
        """
        caminho = self.obter_caminho_arquivo()
        if not caminho.exists():
            return self.obter_dados_iniciais()

        with caminho.open("r", encoding="utf-8") as arquivo:
            return json.load(arquivo)

    def _escrever_dados_sem_lock(self, dados: dict[str, Any]) -> None:
        """
        Persiste o estado completo do banco local no disco.
        """
        caminho = self.obter_caminho_arquivo()
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with caminho.open("w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)

    async def inicializar(self) -> None:
        """
        Garante a existencia do arquivo JSON de persistencia.
        """
        async with self._lock:
            caminho = self.obter_caminho_arquivo()
            if caminho.exists():
                return
            self._escrever_dados_sem_lock(self.obter_dados_iniciais())
            logger.info(f"Banco JSON inicializado em {caminho}.")

    async def listar_registros(self, colecao: str) -> list[dict[str, Any]]:
        """
        Retorna uma copia dos registros de uma colecao.
        """
        async with self._lock:
            dados = self._ler_dados_sem_lock()
            return deepcopy(dados.get(colecao, []))

    async def obter_registro_por_id(self, colecao: str, registro_id: int) -> Optional[dict[str, Any]]:
        """
        Busca um registro por ID em uma colecao.
        """
        async with self._lock:
            dados = self._ler_dados_sem_lock()
            for registro in dados.get(colecao, []):
                if int(registro["id"]) == int(registro_id):
                    return deepcopy(registro)
            return None

    async def obter_primeiro(self, colecao: str, predicado: Callable[[dict[str, Any]], bool]) -> Optional[dict[str, Any]]:
        """
        Busca o primeiro registro de uma colecao que satisfaz um predicado.
        """
        async with self._lock:
            dados = self._ler_dados_sem_lock()
            for registro in dados.get(colecao, []):
                if predicado(registro):
                    return deepcopy(registro)
            return None

    async def inserir_registro(self, colecao: str, registro: dict[str, Any]) -> dict[str, Any]:
        """
        Insere um novo registro em uma colecao gerando um ID incremental.
        """
        async with self._lock:
            dados = self._ler_dados_sem_lock()
            proximo_id = int(dados["sequencias"].get(colecao, 0)) + 1
            dados["sequencias"][colecao] = proximo_id

            novo_registro = deepcopy(registro)
            novo_registro["id"] = proximo_id
            dados.setdefault(colecao, []).append(novo_registro)

            self._escrever_dados_sem_lock(dados)
            return deepcopy(novo_registro)

    async def atualizar_registro(self, colecao: str, registro_id: int, registro_atualizado: dict[str, Any]) -> dict[str, Any]:
        """
        Substitui integralmente um registro existente pelo novo estado informado.
        """
        async with self._lock:
            dados = self._ler_dados_sem_lock()
            for indice, registro in enumerate(dados.get(colecao, [])):
                if int(registro["id"]) == int(registro_id):
                    dados[colecao][indice] = deepcopy(registro_atualizado)
                    self._escrever_dados_sem_lock(dados)
                    return deepcopy(dados[colecao][indice])
        raise ValueError(f"Registro {registro_id} nao encontrado em {colecao}.")

    async def remover_registro(self, colecao: str, registro_id: int) -> dict[str, Any]:
        """
        Remove um unico registro identificado pelo ID e devolve seu conteudo anterior.
        """
        async with self._lock:
            dados = self._ler_dados_sem_lock()
            for indice, registro in enumerate(dados.get(colecao, [])):
                if int(registro["id"]) == int(registro_id):
                    registro_removido = dados[colecao].pop(indice)
                    self._escrever_dados_sem_lock(dados)
                    return deepcopy(registro_removido)
        raise ValueError(f"Registro {registro_id} nao encontrado em {colecao}.")

    async def remover_por_predicado(self, colecao: str, predicado: Callable[[dict[str, Any]], bool]) -> list[dict[str, Any]]:
        """
        Remove todos os registros de uma colecao que satisfazem o predicado informado.
        """
        async with self._lock:
            dados = self._ler_dados_sem_lock()
            registros_atuais = dados.get(colecao, [])
            registros_mantidos: list[dict[str, Any]] = []
            registros_removidos: list[dict[str, Any]] = []

            for registro in registros_atuais:
                if predicado(registro):
                    registros_removidos.append(deepcopy(registro))
                else:
                    registros_mantidos.append(registro)

            if registros_removidos:
                dados[colecao] = registros_mantidos
                self._escrever_dados_sem_lock(dados)

            return registros_removidos

    async def resetar(self) -> None:
        """
        Recria o arquivo do banco local com a estrutura vazia.
        """
        async with self._lock:
            self._escrever_dados_sem_lock(self.obter_dados_iniciais())


banco_json = BancoJsonLocal()
