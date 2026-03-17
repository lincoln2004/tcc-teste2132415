from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
from app.configuracoes.configuracoes import configuracoes

# Configuração do contexto de hashing de senhas (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Algoritmo usado para assinar o JWT
ALGORITHM = "HS256"

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """
    Compara uma senha em texto plano com um hash armazenado.
    Retorna True se coincidirem, False caso contrário.
    """
    return pwd_context.verify(senha_plana, senha_hash)

def obter_hash_senha(senha: str) -> str:
    """
    Gera um hash seguro a partir de uma senha em texto plano.
    Utilizado no momento do cadastro do usuário.
    """
    return pwd_context.hash(senha)

def criar_token_acesso(sujeito: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Gera um token JWT para autenticação do usuário.
    O 'sujeito' geralmente é o ID ou e-mail do usuário.
    O token expira após o tempo definido nas configurações.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=configuracoes.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(sujeito)}
    encoded_jwt = jwt.encode(to_encode, configuracoes.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decodificar_token(token: str) -> Optional[str]:
    """
    Decodifica um token JWT e extrai o sujeito (sub).
    Retorna o valor do sujeito se o token for válido, None caso contrário.
    """
    try:
        payload = jwt.decode(token, configuracoes.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except (jwt.JWTError, AttributeError):
        return None
