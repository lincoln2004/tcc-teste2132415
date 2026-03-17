from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencias.autenticacao import obter_usuario_atual
from app.configuracoes.configuracoes import configuracoes
from app.esquemas.usuario_esquema import Token, UsuarioCriar, UsuarioResposta
from app.modelos.usuario import Usuario
from app.repositorios.usuario_repositorio import UsuarioRepositorio
from app.seguranca.autenticacao import criar_token_acesso, verificar_senha
from app.seguranca.limitador_requisicoes import limitador_auth


router = APIRouter()


def obter_identificador_requisicao(request: Request, identificador_extra: str = "") -> str:
    """
    Gera uma chave simples por origem para aplicar limitacao de tentativas.
    """
    host = request.client.host if request.client else "desconhecido"
    return f"{host}:{identificador_extra}" if identificador_extra else host


@router.post("/cadastro", response_model=UsuarioResposta, status_code=status.HTTP_201_CREATED)
async def cadastrar_usuario(usuario_in: UsuarioCriar, request: Request) -> UsuarioResposta:
    """
    Cria um novo usuario garantindo unicidade de e-mail e limitando abuso por IP.
    """
    chave_rate_limit = obter_identificador_requisicao(request, "cadastro")

    try:
        limitador_auth.registrar_tentativa(
            chave_rate_limit,
            configuracoes.LIMITE_TENTATIVAS_CADASTRO,
            configuracoes.JANELA_TENTATIVAS_AUTH_SEGUNDOS,
        )
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(erro)) from erro

    usuario_existente = await UsuarioRepositorio.obter_por_email(usuario_in.email)
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe um usuario cadastrado com este e-mail.",
        )

    try:
        usuario = await UsuarioRepositorio.criar(usuario_in)
    except ValueError as erro:
        mensagem_erro = str(erro)
        status_http = (
            status.HTTP_409_CONFLICT
            if mensagem_erro == "Ja existe um usuario cadastrado com este e-mail."
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_http, detail=mensagem_erro) from erro

    limitador_auth.limpar_tentativas(chave_rate_limit)
    return usuario


@router.post("/login", response_model=Token)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """
    Autentica um usuario a partir de e-mail e senha e retorna um token JWT.
    """
    chave_rate_limit = obter_identificador_requisicao(request, "login")

    try:
        limitador_auth.registrar_tentativa(
            chave_rate_limit,
            configuracoes.LIMITE_TENTATIVAS_LOGIN,
            configuracoes.JANELA_TENTATIVAS_AUTH_SEGUNDOS,
        )
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(erro)) from erro

    usuario = await UsuarioRepositorio.obter_por_email(form_data.username)
    if not usuario or not verificar_senha(form_data.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.esta_ativo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inativo.")

    access_token_expires = timedelta(minutes=configuracoes.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = criar_token_acesso(sujeito=usuario.id, expires_delta=access_token_expires)
    limitador_auth.limpar_tentativas(chave_rate_limit)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UsuarioResposta)
async def obter_me(usuario_atual: Usuario = Depends(obter_usuario_atual)) -> UsuarioResposta:
    """
    Retorna o perfil do usuario autenticado para o frontend restaurar a sessao.
    """
    return usuario_atual
