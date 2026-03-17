from pathlib import Path

from fastapi.testclient import TestClient

from app.configuracoes.configuracoes import configuracoes


def obter_headers_autenticacao(cliente: TestClient) -> dict[str, str]:
    """
    Cria um usuario de teste e retorna o cabecalho Authorization para uso nas rotas protegidas.
    """
    cliente.post(
        "/api/v1/auth/cadastro",
        json={
            "nome": "Usuario Historico",
            "email": "historico@exemplo.com",
            "senha": "Senha1234",
        },
    )

    resposta_login = cliente.post(
        "/api/v1/auth/login",
        data={
            "username": "historico@exemplo.com",
            "password": "Senha1234",
        },
    )

    token = resposta_login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def criar_dataset(cliente: TestClient, headers: dict[str, str]) -> int:
    """
    Envia um dataset simples para permitir a criacao de analises de teste.
    """
    conteudo_csv = (
        "valor_a,valor_b\n"
        "10,100\n"
        "11,101\n"
        "12,102\n"
        "13,103\n"
        "500,900\n"
    )

    resposta_upload = cliente.post(
        "/api/v1/datasets/upload",
        data={"nome": "Dataset historico", "descricao": "Base para limpar historico"},
        files={"arquivo": ("dados.csv", conteudo_csv.encode("utf-8"), "text/csv")},
        headers=headers,
    )

    assert resposta_upload.status_code == 201
    return int(resposta_upload.json()["id"])


def criar_analise(cliente: TestClient, headers: dict[str, str], dataset_id: int, nome: str) -> int:
    """
    Cria uma analise concluida para alimentar o historico do usuario.
    """
    resposta_analise = cliente.post(
        "/api/v1/analises/executar",
        json={
            "nome": nome,
            "algoritmo": "zscore",
            "tipo_algoritmo": "estatistico",
            "dataset_id": dataset_id,
            "colunas_selecionadas": ["valor_a", "valor_b"],
            "parametros": {"threshold": 2.0},
        },
        headers=headers,
    )

    assert resposta_analise.status_code == 201
    return int(resposta_analise.json()["id"])


def test_excluir_historico_remove_analises_e_arquivos_csv(cliente: TestClient) -> None:
    """
    Garante que a exclusao em massa do historico remova registros e arquivos de resultado.
    """
    headers = obter_headers_autenticacao(cliente)
    dataset_id = criar_dataset(cliente, headers)

    analise_id_1 = criar_analise(cliente, headers, dataset_id, "Analise historico 1")
    analise_id_2 = criar_analise(cliente, headers, dataset_id, "Analise historico 2")

    arquivos_resultado_antes = sorted(Path(configuracoes.UPLOAD_DIR).glob("resultado_analise_*.csv"))
    assert len(arquivos_resultado_antes) == 2

    resposta_exclusao = cliente.delete("/api/v1/analises/historico", headers=headers)

    assert resposta_exclusao.status_code == 200
    assert resposta_exclusao.json()["analises_removidas"] == 2

    resposta_historico = cliente.get("/api/v1/analises/historico", headers=headers)
    assert resposta_historico.status_code == 200
    assert resposta_historico.json() == []

    assert cliente.get(f"/api/v1/analises/{analise_id_1}", headers=headers).status_code == 404
    assert cliente.get(f"/api/v1/analises/{analise_id_2}", headers=headers).status_code == 404
    assert list(Path(configuracoes.UPLOAD_DIR).glob("resultado_analise_*.csv")) == []
