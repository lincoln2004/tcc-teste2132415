from fastapi.testclient import TestClient

from app.configuracoes.configuracoes import configuracoes

def test_fluxo_cadastro_login_e_me(cliente: TestClient) -> None:
    """
    Garante que um usuario consegue se cadastrar, autenticar e recuperar o proprio perfil.
    """
    resposta_cadastro = cliente.post(
        "/api/v1/auth/cadastro",
        json={
            "nome": "Usuario Teste",
            "email": "teste@exemplo.com",
            "senha": "Senha1234",
        },
    )

    assert resposta_cadastro.status_code == 201
    assert resposta_cadastro.json()["email"] == "teste@exemplo.com"

    resposta_login = cliente.post(
        "/api/v1/auth/login",
        data={
            "username": "teste@exemplo.com",
            "password": "Senha1234",
        },
    )

    assert resposta_login.status_code == 200
    token = resposta_login.json()["access_token"]

    resposta_me = cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta_me.status_code == 200
    assert resposta_me.json()["nome"] == "Usuario Teste"


def test_nao_permitem_email_duplicado(cliente: TestClient) -> None:
    """
    Garante que o mesmo e-mail nao pode ser cadastrado duas vezes.
    """
    payload = {
        "nome": "Usuario Duplicado",
        "email": "duplicado@exemplo.com",
        "senha": "Senha1234",
    }

    primeira = cliente.post("/api/v1/auth/cadastro", json=payload)
    segunda = cliente.post("/api/v1/auth/cadastro", json=payload)

    assert primeira.status_code == 201
    assert segunda.status_code == 409
    assert segunda.json()["detail"] == "Ja existe um usuario cadastrado com este e-mail."


def test_limita_tentativas_de_login_invalido(cliente: TestClient) -> None:
    """
    Garante que varias tentativas invalidas consecutivas sejam bloqueadas temporariamente.
    """
    cliente.post(
        "/api/v1/auth/cadastro",
        json={
            "nome": "Usuario Bloqueio",
            "email": "bloqueio@exemplo.com",
            "senha": "Senha1234",
        },
    )

    for _ in range(configuracoes.LIMITE_TENTATIVAS_LOGIN):
        resposta = cliente.post(
            "/api/v1/auth/login",
            data={
                "username": "bloqueio@exemplo.com",
                "password": "senha_errada",
            },
        )
        assert resposta.status_code == 401

    resposta_bloqueio = cliente.post(
        "/api/v1/auth/login",
        data={
            "username": "bloqueio@exemplo.com",
            "password": "senha_errada",
        },
    )

    assert resposta_bloqueio.status_code == 429
    assert "Muitas tentativas" in resposta_bloqueio.json()["detail"]
