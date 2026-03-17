from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.configuracoes.configuracoes import configuracoes
from app.modelos.usuario import Usuario
from app.repositorios.usuario_repositorio import UsuarioRepositorio
from app.seguranca.autenticacao import decodificar_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{configuracoes.API_V1_STR}/auth/login")


async def obter_usuario_atual(token: str = Depends(oauth2_scheme)) -> Usuario:
    """
    Resolve o usuario autenticado a partir do token JWT enviado pelo cliente.
    """
    sujeito = decodificar_token(token)
    if not sujeito:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacao invalido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        usuario_id = int(sujeito)
    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacao invalido.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from erro

    usuario = await UsuarioRepositorio.obter_por_id(usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario autenticado nao foi encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.esta_ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inativo.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return usuario
