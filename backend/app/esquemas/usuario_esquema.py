from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UsuarioBase(BaseModel):
    """
    Campos compartilhados pelos esquemas de usuario.
    """

    nome: str = Field(..., min_length=3, max_length=100, description="Nome completo do usuario")
    email: EmailStr = Field(..., description="Endereco de e-mail unico")

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, nome: str) -> str:
        """
        Remove espacos excedentes e garante um nome minimamente valido.
        """
        nome_normalizado = " ".join(nome.split())
        if len(nome_normalizado) < 3:
            raise ValueError("O nome deve ter no minimo 3 caracteres.")
        return nome_normalizado

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, email: EmailStr) -> str:
        """
        Normaliza o e-mail para evitar duplicidades por diferenca de caixa.
        """
        return str(email).strip().lower()


class UsuarioCriar(UsuarioBase):
    """
    Esquema de entrada para cadastro de um novo usuario.
    """

    senha: str = Field(..., min_length=8, description="Senha com no minimo 8 caracteres")

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, senha: str) -> str:
        """
        Aplica validacoes basicas de seguranca antes de salvar a senha.
        """
        senha_normalizada = senha.strip()
        if len(senha_normalizada) < 8:
            raise ValueError("A senha deve ter no minimo 8 caracteres.")
        if not any(caractere.isalpha() for caractere in senha_normalizada):
            raise ValueError("A senha deve conter ao menos uma letra.")
        if not any(caractere.isdigit() for caractere in senha_normalizada):
            raise ValueError("A senha deve conter ao menos um numero.")
        return senha_normalizada


class UsuarioAtualizar(BaseModel):
    """
    Esquema usado para futuras atualizacoes de dados do usuario.
    """

    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    senha: Optional[str] = None


class UsuarioResposta(UsuarioBase):
    """
    Esquema de saida publico do usuario sem expor a senha.
    """

    id: int
    esta_ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """
    Token JWT retornado no login.
    """

    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """
    Conteudo minimo esperado no payload do token.
    """

    sub: Optional[str] = None
