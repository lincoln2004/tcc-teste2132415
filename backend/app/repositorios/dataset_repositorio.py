from app.banco.banco_json import banco_json
from app.modelos.dataset import Dataset


class DatasetRepositorio:
    """
    Repositorio responsavel pela persistencia local de datasets.
    """

    @staticmethod
    async def criar(
        *,
        nome: str,
        descricao: str | None,
        caminho_arquivo: str,
        formato: str,
        tamanho_bytes: int,
        metadados: dict | None,
        usuario_id: int,
    ) -> Dataset:
        """
        Persiste um novo dataset no banco local em JSON.
        """
        registro = Dataset.novo(
            id=0,
            nome=nome,
            descricao=descricao,
            caminho_arquivo=caminho_arquivo,
            formato=formato,
            tamanho_bytes=tamanho_bytes,
            metadados=metadados,
            usuario_id=usuario_id,
        )
        dados = await banco_json.inserir_registro("datasets", registro.para_dict())
        return Dataset.de_dict(dados)

    @staticmethod
    async def listar_por_usuario(usuario_id: int) -> list[Dataset]:
        """
        Lista os datasets de um usuario em ordem decrescente de criacao.
        """
        registros = await banco_json.listar_registros("datasets")
        datasets = [Dataset.de_dict(item) for item in registros if int(item["usuario_id"]) == int(usuario_id)]
        return sorted(datasets, key=lambda dataset: dataset.criado_em, reverse=True)

    @staticmethod
    async def obter_por_id(dataset_id: int) -> Dataset | None:
        """
        Busca um dataset pelo identificador.
        """
        dados = await banco_json.obter_registro_por_id("datasets", dataset_id)
        return Dataset.de_dict(dados) if dados else None

    @staticmethod
    async def obter_por_id_e_usuario(dataset_id: int, usuario_id: int) -> Dataset | None:
        """
        Busca um dataset garantindo que ele pertence ao usuario informado.
        """
        dados = await banco_json.obter_primeiro(
            "datasets",
            lambda item: int(item["id"]) == int(dataset_id) and int(item["usuario_id"]) == int(usuario_id),
        )
        return Dataset.de_dict(dados) if dados else None

    @staticmethod
    async def remover_por_id_e_usuario(dataset_id: int, usuario_id: int) -> Dataset | None:
        """
        Remove um dataset somente quando ele pertence ao usuario autenticado.
        """
        dataset = await DatasetRepositorio.obter_por_id_e_usuario(dataset_id, usuario_id)
        if not dataset:
            return None

        dados = await banco_json.remover_registro("datasets", dataset.id)
        return Dataset.de_dict(dados)
