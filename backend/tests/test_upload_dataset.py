from fastapi.testclient import TestClient


def obter_headers_autenticacao(cliente: TestClient) -> dict[str, str]:
    """
    Cadastra um usuario de teste e retorna o cabecalho Authorization para as requisicoes protegidas.
    """
    cliente.post(
        "/api/v1/auth/cadastro",
        json={
            "nome": "Usuario Dataset",
            "email": "dataset@exemplo.com",
            "senha": "Senha1234",
        },
    )

    resposta_login = cliente.post(
        "/api/v1/auth/login",
        data={
            "username": "dataset@exemplo.com",
            "password": "Senha1234",
        },
    )

    token = resposta_login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_csv_descarta_linha_malformada_e_salva_dataset(cliente: TestClient) -> None:
    """
    Garante que uma linha CSV com quantidade incorreta de campos seja descartada sem derrubar o upload.
    """
    headers = obter_headers_autenticacao(cliente)
    conteudo_csv = (
        "coluna_a,coluna_b,coluna_c,coluna_d\n"
        "1,2,3,4\n"
        "5,6,7,8,9\n"
        "10,11,12,13\n"
    )

    resposta = cliente.post(
        "/api/v1/datasets/upload",
        data={"nome": "Dataset com linha invalida", "descricao": "Teste de upload tolerante"},
        files={"arquivo": ("dados.csv", conteudo_csv.encode("utf-8"), "text/csv")},
        headers=headers,
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["metadados"]["total_linhas"] == 2
    assert corpo["metadados"]["linhas_descartadas"] == 1
    assert corpo["metadados"]["linhas_com_problema"] == [3]
    assert "Foram descartadas 1 linha(s)" in corpo["metadados"]["aviso_importacao"]


def test_upload_csv_detecta_separador_ponto_e_virgula(cliente: TestClient) -> None:
    """
    Garante que CSVs separados por ponto e virgula sejam interpretados corretamente.
    """
    headers = obter_headers_autenticacao(cliente)
    conteudo_csv = (
        "nome;idade;salario\n"
        "Ana;30;1000\n"
        "Bruno;35;1200\n"
    )

    resposta = cliente.post(
        "/api/v1/datasets/upload",
        data={"nome": "Dataset com ponto e virgula", "descricao": "Teste de separador"},
        files={"arquivo": ("dados.csv", conteudo_csv.encode("utf-8"), "text/csv")},
        headers=headers,
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["metadados"]["total_linhas"] == 2
    assert corpo["metadados"]["linhas_descartadas"] == 0
    assert corpo["metadados"]["separador"] == ";"
    assert [coluna["nome"] for coluna in corpo["metadados"]["colunas"]] == ["nome", "idade", "salario"]
