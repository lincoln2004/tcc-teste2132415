from typing import Optional

from app.banco.banco_json import banco_json
from app.esquemas.usuario_esquema import UsuarioCriar
from app.modelos.usuario import Usuario
from app.seguranca.autenticacao import obter_hash_senha


class UsuarioRepositorio:
    """
    Repositorio responsavel pela persistencia local de usuarios em JSON.
    """

    @staticmethod
    async def obter_por_email(email: str) -> Optional[Usuario]:
        """
        Busca um usuario pelo e-mail ja normalizado.
        """
        dados = await banco_json.obter_primeiro(
            "usuarios",
            lambda item: item["email"] == email.strip().lower(),
        )
        return Usuario.de_dict(dados) if dados else None

    @staticmethod
    async def obter_por_id(usuario_id: int) -> Optional[Usuario]:
        """
        Busca um usuario pelo identificador primario.
        """
        dados = await banco_json.obter_registro_por_id("usuarios", usuario_id)
        return Usuario.de_dict(dados) if dados else None

    @staticmethod
    async def criar(usuario_in: UsuarioCriar) -> Usuario:
        """
        Cria um novo usuario persistindo a senha em formato hash seguro.
        """
        usuario_existente = await UsuarioRepositorio.obter_por_email(usuario_in.email)
        if usuario_existente:
            raise ValueError("Ja existe um usuario cadastrado com este e-mail.")

        novo_usuario = Usuario.novo(
            id=0,
            nome=usuario_in.nome,
            email=usuario_in.email,
            senha_hash=obter_hash_senha(usuario_in.senha),
        )
        dados = await banco_json.inserir_registro("usuarios", novo_usuario.para_dict())
        return Usuario.de_dict(dados)
