from dataclasses import dataclass

from app.modelos.base_modelo import BaseModelo, desserializar_data


@dataclass(kw_only=True)
class Usuario(BaseModelo):
    """
    Modelo local de usuario persistido no arquivo JSON.
    """

    nome: str
    email: str
    senha_hash: str
    esta_ativo: bool = True
    e_superusuario: bool = False

    @classmethod
    def novo(cls, *, id: int, nome: str, email: str, senha_hash: str) -> "Usuario":
        """
        Cria uma nova instancia de usuario com valores padrao de seguranca.
        """
        return cls(id=id, nome=nome, email=email, senha_hash=senha_hash)

    @classmethod
    def de_dict(cls, dados: dict) -> "Usuario":
        """
        Reconstrui um usuario a partir do registro armazenado em JSON.
        """
        return cls(
            id=int(dados["id"]),
            nome=dados["nome"],
            email=dados["email"],
            senha_hash=dados["senha_hash"],
            esta_ativo=bool(dados.get("esta_ativo", True)),
            e_superusuario=bool(dados.get("e_superusuario", False)),
            criado_em=desserializar_data(dados["criado_em"]),
            atualizado_em=desserializar_data(dados["atualizado_em"]),
        )
