from app.banco.banco_json import banco_json
from app.modelos.analise import Analise


class AnaliseRepositorio:
    """
    Repositorio responsavel pela persistencia local das analises.
    """

    @staticmethod
    async def criar(
        *,
        nome: str,
        algoritmo: str,
        tipo_algoritmo: str,
        parametros: dict | None,
        colunas_selecionadas: list[str],
        status: str,
        usuario_id: int,
        dataset_id: int,
    ) -> Analise:
        """
        Persiste uma nova analise no banco local.
        """
        registro = Analise.novo(
            id=0,
            nome=nome,
            algoritmo=algoritmo,
            tipo_algoritmo=tipo_algoritmo,
            parametros=parametros,
            colunas_selecionadas=colunas_selecionadas,
            status=status,
            usuario_id=usuario_id,
            dataset_id=dataset_id,
        )
        dados = await banco_json.inserir_registro("analises", registro.para_dict())
        return Analise.de_dict(dados)

    @staticmethod
    async def atualizar(analise: Analise) -> Analise:
        """
        Salva o estado atual de uma analise ja existente.
        """
        analise.tocar()
        dados = await banco_json.atualizar_registro("analises", analise.id, analise.para_dict())
        return Analise.de_dict(dados)

    @staticmethod
    async def listar_por_usuario(usuario_id: int) -> list[Analise]:
        """
        Lista as analises de um usuario em ordem decrescente de criacao.
        """
        registros = await banco_json.listar_registros("analises")
        analises = [Analise.de_dict(item) for item in registros if int(item["usuario_id"]) == int(usuario_id)]
        return sorted(analises, key=lambda analise: analise.criado_em, reverse=True)

    @staticmethod
    async def obter_por_id(analise_id: int) -> Analise | None:
        """
        Busca uma analise pelo identificador.
        """
        dados = await banco_json.obter_registro_por_id("analises", analise_id)
        return Analise.de_dict(dados) if dados else None

    @staticmethod
    async def obter_por_id_e_usuario(analise_id: int, usuario_id: int) -> Analise | None:
        """
        Busca uma analise assegurando o ownership do usuario autenticado.
        """
        dados = await banco_json.obter_primeiro(
            "analises",
            lambda item: int(item["id"]) == int(analise_id) and int(item["usuario_id"]) == int(usuario_id),
        )
        return Analise.de_dict(dados) if dados else None

    @staticmethod
    async def listar_por_dataset_e_usuario(dataset_id: int, usuario_id: int) -> list[Analise]:
        """
        Lista as analises vinculadas a um dataset especifico do usuario informado.
        """
        registros = await banco_json.listar_registros("analises")
        analises = [
            Analise.de_dict(item)
            for item in registros
            if int(item["dataset_id"]) == int(dataset_id) and int(item["usuario_id"]) == int(usuario_id)
        ]
        return sorted(analises, key=lambda analise: analise.criado_em, reverse=True)

    @staticmethod
    async def remover_por_dataset_e_usuario(dataset_id: int, usuario_id: int) -> list[Analise]:
        """
        Remove todas as analises associadas ao dataset do usuario autenticado.
        """
        dados_removidos = await banco_json.remover_por_predicado(
            "analises",
            lambda item: int(item["dataset_id"]) == int(dataset_id) and int(item["usuario_id"]) == int(usuario_id),
        )
        return [Analise.de_dict(item) for item in dados_removidos]

    @staticmethod
    async def remover_por_usuario(usuario_id: int) -> list[Analise]:
        """
        Remove todo o historico de analises pertencente ao usuario autenticado.
        """
        dados_removidos = await banco_json.remover_por_predicado(
            "analises",
            lambda item: int(item["usuario_id"]) == int(usuario_id),
        )
        return [Analise.de_dict(item) for item in dados_removidos]
