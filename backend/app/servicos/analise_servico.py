import os

import numpy as np
from loguru import logger

from app.algoritmos.estatisticos.metodos_estatisticos import IQRDeteccao, ZScoreDeteccao
from app.algoritmos.machine_learning.metodos_ml import IsolationForestDeteccao, LocalOutlierFactorDeteccao
from app.configuracoes.configuracoes import configuracoes
from app.esquemas.analise_esquema import AnaliseCriar
from app.servicos.detalhamento_analise import DetalhadorAnalise
from app.repositorios.analise_repositorio import AnaliseRepositorio
from app.repositorios.dataset_repositorio import DatasetRepositorio
from app.processamento.limpeza_dados import ProcessadorDados


class AnaliseServico:
    """
    Servico de orquestracao de analises com persistencia local em JSON.
    """

    PARAMETROS_PADRAO = {
        "zscore": {"threshold": 3.0},
        "iqr": {"fator": 1.5},
        "isolation_forest": {"contaminacao": 0.05, "n_estimadores": 100},
        "lof": {"contaminacao": 0.05, "n_vizinhos": 20},
    }

    ALGORITMOS = {
        "zscore": ZScoreDeteccao(),
        "iqr": IQRDeteccao(),
        "isolation_forest": IsolationForestDeteccao(),
        "lof": LocalOutlierFactorDeteccao(),
    }

    @staticmethod
    def obter_parametros_efetivos(algoritmo: str, parametros_informados: dict | None) -> dict:
        """
        Mescla os parametros informados com os valores padrao esperados pelo algoritmo.
        """
        parametros_padrao = AnaliseServico.PARAMETROS_PADRAO.get(algoritmo, {})
        return {**parametros_padrao, **(parametros_informados or {})}

    @staticmethod
    def remover_arquivo_resultado_se_existir(caminho_arquivo: str | None) -> None:
        """
        Remove o arquivo CSV de resultado quando ele existir no armazenamento local.
        """
        if not caminho_arquivo:
            return

        try:
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
        except OSError as erro:
            logger.warning(f"Nao foi possivel remover o arquivo de resultado '{caminho_arquivo}': {erro}")

    @staticmethod
    async def criar_e_executar_analise(analise_in: AnaliseCriar, usuario_id: int):
        """
        Cria o registro da analise no banco local e executa o algoritmo solicitado.
        """
        dataset = await DatasetRepositorio.obter_por_id_e_usuario(analise_in.dataset_id, usuario_id)
        if not dataset:
            raise ValueError("Dataset nao encontrado para o usuario informado.")

        parametros_efetivos = AnaliseServico.obter_parametros_efetivos(
            analise_in.algoritmo,
            analise_in.parametros,
        )

        nova_analise = await AnaliseRepositorio.criar(
            nome=analise_in.nome,
            algoritmo=analise_in.algoritmo,
            tipo_algoritmo=analise_in.tipo_algoritmo,
            parametros=parametros_efetivos,
            colunas_selecionadas=analise_in.colunas_selecionadas,
            status="processando",
            usuario_id=usuario_id,
            dataset_id=analise_in.dataset_id,
        )

        try:
            df_original = ProcessadorDados.carregar_arquivo(dataset.caminho_arquivo, dataset.formato)
            df_limpo = ProcessadorDados.limpar_dados(df_original, analise_in.colunas_selecionadas)

            if analise_in.tipo_algoritmo == "machine_learning":
                df_processado = ProcessadorDados.normalizar_dados(df_limpo)
            else:
                df_processado = df_limpo

            algoritmo_instancia = AnaliseServico.ALGORITMOS.get(analise_in.algoritmo)
            if not algoritmo_instancia:
                raise ValueError(f"Algoritmo {analise_in.algoritmo} nao implementado.")

            flags, scores = algoritmo_instancia.treinar_e_prever(df_processado, parametros_efetivos)
            flags_array = np.asarray(flags, dtype=int)
            scores_array = np.nan_to_num(np.asarray(scores, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)

            df_resultado = df_original.copy()
            df_resultado["anomalia_flag"] = flags_array
            df_resultado["anomalia_score"] = scores_array

            nome_arquivo_resultado = f"resultado_analise_{nova_analise.id}.csv"
            caminho_resultado = os.path.join(configuracoes.UPLOAD_DIR, nome_arquivo_resultado)
            df_resultado.to_csv(caminho_resultado, index=False)

            nova_analise.status = "concluido"
            nova_analise.resultado_resumo = DetalhadorAnalise.construir_resultado_resumo(
                analise_in.algoritmo,
                df_original,
                df_limpo,
                flags_array,
                scores_array,
                parametros_efetivos,
            )
            nova_analise.caminho_resultado_csv = caminho_resultado

            analise_atualizada = await AnaliseRepositorio.atualizar(nova_analise)
            logger.info(f"Analise {analise_atualizada.id} concluida com sucesso.")
            return analise_atualizada
        except Exception as erro:
            logger.error(f"Erro ao executar analise {nova_analise.id}: {erro}")
            nova_analise.status = "erro"
            nova_analise.resultado_resumo = {"erro": str(erro)}
            await AnaliseRepositorio.atualizar(nova_analise)
            raise

    @staticmethod
    async def excluir_historico_usuario(usuario_id: int) -> dict[str, int | str]:
        """
        Remove todas as analises do usuario autenticado e limpa os arquivos CSV gerados.
        """
        analises_removidas = await AnaliseRepositorio.remover_por_usuario(usuario_id)

        for analise in analises_removidas:
            AnaliseServico.remover_arquivo_resultado_se_existir(analise.caminho_resultado_csv)

        logger.info(
            f"Historico do usuario {usuario_id} excluido com sucesso. "
            f"Foram removidas {len(analises_removidas)} analise(s)."
        )

        return {
            "mensagem": "Historico excluido com sucesso.",
            "analises_removidas": len(analises_removidas),
        }
