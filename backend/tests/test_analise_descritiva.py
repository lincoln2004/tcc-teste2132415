import pytest
from fastapi.testclient import TestClient


def obter_headers_autenticacao(cliente: TestClient, email: str) -> dict[str, str]:
    """
    Cria um usuario de teste e retorna o cabecalho Authorization pronto para uso.
    """
    cliente.post(
        "/api/v1/auth/cadastro",
        json={
            "nome": "Usuario Analise",
            "email": email,
            "senha": "Senha1234",
        },
    )

    resposta_login = cliente.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "Senha1234",
        },
    )

    token = resposta_login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def criar_dataset_com_anomalias(cliente: TestClient, headers: dict[str, str]) -> int:
    """
    Envia um dataset simples com dois registros extremamente distantes para exercitar todos os modelos.
    """
    linhas_normais = [f"{10 + indice},{100 + indice}" for indice in range(20)]
    linhas_anomalas = [
        "500,900",
        "520,940",
    ]
    conteudo_csv = "valor_a,valor_b\n" + "\n".join(linhas_normais + linhas_anomalas) + "\n"

    resposta_upload = cliente.post(
        "/api/v1/datasets/upload",
        data={"nome": "Dataset Analise Descritiva", "descricao": "Teste dos detalhes das anomalias"},
        files={"arquivo": ("analise.csv", conteudo_csv.encode("utf-8"), "text/csv")},
        headers=headers,
    )

    assert resposta_upload.status_code == 201
    return int(resposta_upload.json()["id"])


@pytest.mark.parametrize(
    ("algoritmo", "tipo_algoritmo", "parametros", "prefixo_tipo"),
    [
        ("zscore", "estatistico", {"threshold": 2.5}, "zscore_"),
        ("iqr", "estatistico", {"fator": 1.5}, "iqr_"),
        ("isolation_forest", "machine_learning", {"contaminacao": 0.08, "n_estimadores": 50}, "isolation_forest_"),
        ("lof", "machine_learning", {"contaminacao": 0.08, "n_vizinhos": 5}, "lof_"),
    ],
)
def test_resultado_resumo_traz_explicacao_detalhada_por_modelo(
    cliente: TestClient,
    algoritmo: str,
    tipo_algoritmo: str,
    parametros: dict[str, float | int],
    prefixo_tipo: str,
) -> None:
    """
    Garante que todos os modelos retornem onde, por que e qual tipo de anomalia foi encontrado.
    """
    headers = obter_headers_autenticacao(cliente, f"{algoritmo}@exemplo.com")
    dataset_id = criar_dataset_com_anomalias(cliente, headers)

    resposta_analise = cliente.post(
        "/api/v1/analises/executar",
        json={
            "nome": f"Analise {algoritmo}",
            "algoritmo": algoritmo,
            "tipo_algoritmo": tipo_algoritmo,
            "dataset_id": dataset_id,
            "colunas_selecionadas": ["valor_a", "valor_b"],
            "parametros": parametros,
        },
        headers=headers,
    )

    assert resposta_analise.status_code == 201
    corpo = resposta_analise.json()
    resumo = corpo["resultado_resumo"]

    assert corpo["status"] == "concluido"
    assert resumo["total_registros"] == 22
    assert resumo["total_anomalias"] >= 1
    assert resumo["interpretacao_geral"]
    assert resumo["parametros_utilizados"] == parametros
    assert resumo["tipos_anomalia_encontrados"]
    assert resumo["dicionario_tipos_anomalia"]
    assert resumo["anomalias_detalhadas"]

    primeira_anomalia = resumo["anomalias_detalhadas"][0]
    primeiro_tipo = resumo["tipos_anomalia_encontrados"][0]
    primeira_coluna = primeira_anomalia["colunas_relevantes"][0]

    assert primeira_anomalia["tipo_principal"].startswith(prefixo_tipo)
    assert primeira_anomalia["tipo_principal_nome"]
    assert primeira_anomalia["localizacao"]
    assert primeira_anomalia["justificativa"]
    assert primeira_anomalia["dados_registro"]["valor_a"] is not None
    assert primeira_coluna["coluna"] in {"valor_a", "valor_b"}
    assert primeira_coluna["motivo"]
    assert primeiro_tipo["codigo"] in resumo["dicionario_tipos_anomalia"]
