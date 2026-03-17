from pathlib import Path

from fastapi.testclient import TestClient

from app.configuracoes.configuracoes import configuracoes


def obter_headers_autenticacao(cliente: TestClient) -> dict[str, str]:
    """
    Cria um usuario de teste e devolve o cabecalho Authorization para as rotas protegidas.
    """
    cliente.post(
        "/api/v1/auth/cadastro",
        json={
            "nome": "Usuario Exclusao",
            "email": "excluir@exemplo.com",
            "senha": "Senha1234",
        },
    )

    resposta_login = cliente.post(
        "/api/v1/auth/login",
        data={
            "username": "excluir@exemplo.com",
            "password": "Senha1234",
        },
    )

    token = resposta_login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_excluir_dataset_remove_registro_analises_e_arquivos(cliente: TestClient) -> None:
    """
    Garante que a exclusao apague o dataset, suas analises vinculadas e os arquivos fisicos locais.
    """
    headers = obter_headers_autenticacao(cliente)
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
        data={"nome": "Dataset para exclusao", "descricao": "Teste de remocao completa"},
        files={"arquivo": ("dados.csv", conteudo_csv.encode("utf-8"), "text/csv")},
        headers=headers,
    )

    assert resposta_upload.status_code == 201
    dataset_id = resposta_upload.json()["id"]

    resposta_analise = cliente.post(
        "/api/v1/analises/executar",
        json={
            "nome": "Analise ligada ao dataset",
            "algoritmo": "zscore",
            "tipo_algoritmo": "estatistico",
            "dataset_id": dataset_id,
            "colunas_selecionadas": ["valor_a", "valor_b"],
            "parametros": {"threshold": 2.0},
        },
        headers=headers,
    )

    assert resposta_analise.status_code == 201
    analise_id = resposta_analise.json()["id"]

    arquivos_antes = list(Path(configuracoes.UPLOAD_DIR).glob("*"))
    assert len(arquivos_antes) == 2

    resposta_exclusao = cliente.delete(f"/api/v1/datasets/{dataset_id}", headers=headers)

    assert resposta_exclusao.status_code == 200
    assert resposta_exclusao.json()["dataset_id"] == dataset_id
    assert resposta_exclusao.json()["analises_removidas"] == 1

    assert cliente.get(f"/api/v1/datasets/{dataset_id}", headers=headers).status_code == 404
    assert cliente.get(f"/api/v1/analises/{analise_id}", headers=headers).status_code == 404
    assert cliente.get("/api/v1/datasets/", headers=headers).json() == []
    assert list(Path(configuracoes.UPLOAD_DIR).glob("*")) == []
