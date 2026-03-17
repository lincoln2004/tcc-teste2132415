import os
import re
import shutil
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import UploadFile
from loguru import logger

from app.configuracoes.configuracoes import configuracoes
from app.processamento.limpeza_dados import ProcessadorDados
from app.repositorios.analise_repositorio import AnaliseRepositorio
from app.repositorios.dataset_repositorio import DatasetRepositorio


class DatasetServico:
    """
    Servico para gestao de datasets com persistencia local em arquivo JSON.
    """

    @staticmethod
    def gerar_nome_arquivo_seguro(usuario_id: int, nome_original: str) -> str:
        """
        Gera um nome de arquivo previsivel e seguro para armazenamento local.
        """
        nome_base = Path(nome_original).name
        nome_normalizado = re.sub(r"[^A-Za-z0-9._-]", "_", nome_base)
        return f"usuario_{usuario_id}_{uuid4().hex[:12]}_{nome_normalizado}"

    @staticmethod
    async def salvar_dataset(
        arquivo: UploadFile,
        nome: str,
        descricao: Optional[str],
        usuario_id: int,
    ):
        """
        Salva o arquivo no disco, extrai metadados e registra no banco JSON local.
        """
        if not arquivo.filename:
            raise ValueError("Nenhum arquivo foi enviado.")

        extensao = arquivo.filename.split(".")[-1].lower()
        if extensao not in ["csv", "xlsx", "xls"]:
            raise ValueError("Formato de arquivo nao suportado. Use CSV ou Excel.")

        arquivo.file.seek(0, os.SEEK_END)
        tamanho_arquivo = arquivo.file.tell()
        arquivo.file.seek(0)

        if tamanho_arquivo > configuracoes.MAX_UPLOAD_SIZE:
            raise ValueError("O arquivo excede o tamanho maximo permitido de 50MB.")

        nome_arquivo_seguro = DatasetServico.gerar_nome_arquivo_seguro(usuario_id, arquivo.filename)
        caminho_completo = os.path.join(configuracoes.UPLOAD_DIR, nome_arquivo_seguro)

        with open(caminho_completo, "wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)

        try:
            df, relatorio_importacao = ProcessadorDados.carregar_arquivo_com_relatorio(caminho_completo, extensao)
            metadados_colunas = ProcessadorDados.extrair_metadados(df)

            dataset = await DatasetRepositorio.criar(
                nome=nome,
                descricao=descricao,
                caminho_arquivo=caminho_completo,
                formato=extensao,
                tamanho_bytes=tamanho_arquivo,
                metadados={
                    "colunas": metadados_colunas,
                    "total_linhas": len(df),
                    **relatorio_importacao,
                },
                usuario_id=usuario_id,
            )

            logger.info(f"Dataset '{nome}' (ID: {dataset.id}) salvo com sucesso.")
            return dataset
        except Exception as erro:
            if os.path.exists(caminho_completo):
                os.remove(caminho_completo)
            logger.error(f"Erro ao processar dataset: {erro}")
            raise

    @staticmethod
    async def listar_datasets(usuario_id: int):
        """
        Retorna todos os datasets de um usuario especifico.
        """
        return await DatasetRepositorio.listar_por_usuario(usuario_id)

    @staticmethod
    def remover_arquivo_se_existir(caminho_arquivo: str | None) -> None:
        """
        Remove um arquivo fisico do disco quando ele ainda existe no armazenamento local.
        """
        if not caminho_arquivo:
            return

        try:
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
        except OSError as erro:
            logger.warning(f"Nao foi possivel remover o arquivo local '{caminho_arquivo}': {erro}")

    @staticmethod
    async def excluir_dataset(dataset_id: int, usuario_id: int) -> dict[str, int | str]:
        """
        Exclui um dataset do usuario autenticado e remove tambem as analises e arquivos derivados.
        """
        dataset = await DatasetRepositorio.obter_por_id_e_usuario(dataset_id, usuario_id)
        if not dataset:
            raise ValueError("Dataset nao encontrado.")

        analises_relacionadas = await AnaliseRepositorio.listar_por_dataset_e_usuario(dataset.id, usuario_id)

        analises_removidas = await AnaliseRepositorio.remover_por_dataset_e_usuario(dataset.id, usuario_id)
        dataset_removido = await DatasetRepositorio.remover_por_id_e_usuario(dataset.id, usuario_id)

        if not dataset_removido:
            raise ValueError("Dataset nao encontrado.")

        DatasetServico.remover_arquivo_se_existir(dataset.caminho_arquivo)
        for analise in analises_relacionadas:
            DatasetServico.remover_arquivo_se_existir(analise.caminho_resultado_csv)

        logger.info(
            f"Dataset '{dataset.nome}' (ID: {dataset.id}) excluido com sucesso "
            f"junto com {len(analises_removidas)} analise(s) relacionada(s)."
        )

        return {
            "mensagem": "Dataset excluido com sucesso.",
            "dataset_id": dataset.id,
            "analises_removidas": len(analises_removidas),
        }
