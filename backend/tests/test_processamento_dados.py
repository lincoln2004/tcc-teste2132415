import pandas as pd
import pytest

from app.processamento.limpeza_dados import ProcessadorDados


def test_limpar_dados_converte_valores_monetarios_e_decimais_textuais() -> None:
    """
    Garante que valores monetarios e numericos com virgula decimal sejam convertidos para float.
    """
    df = pd.DataFrame(
        {
            "minimum cost": ["$43,23", "$50,10", "$39,90"],
            "rate": ["$0,71", "$0,75", "$1,06"],
            "carrier": ["V444_6", "V444_6", "V444_6"],
        }
    )

    df_limpo = ProcessadorDados.limpar_dados(df, ["minimum cost", "rate"])

    assert str(df_limpo["minimum cost"].dtype) == "float64"
    assert str(df_limpo["rate"].dtype) == "float64"
    assert df_limpo["minimum cost"].tolist() == [43.23, 50.10, 39.90]
    assert df_limpo["rate"].tolist() == [0.71, 0.75, 1.06]


def test_limpar_dados_rejeita_coluna_categorica_sem_conversao_numerica() -> None:
    """
    Garante que colunas categoricas nao sejam aceitas silenciosamente na analise.
    """
    df = pd.DataFrame(
        {
            "carrier": ["V444_6", "V555_8", "V999_1"],
        }
    )

    with pytest.raises(ValueError, match="carrier"):
        ProcessadorDados.limpar_dados(df, ["carrier"])


def test_extrair_metadados_reconhece_coluna_textual_numerica() -> None:
    """
    Garante que colunas numericas salvas como texto sejam classificadas como numericas nos metadados.
    """
    df = pd.DataFrame(
        {
            "rate": ["$0,71", "$0,75", "$1,06"],
            "carrier": ["A", "B", "C"],
        }
    )

    metadados = ProcessadorDados.extrair_metadados(df)
    metadados_por_nome = {item["nome"]: item for item in metadados}

    assert "float" in metadados_por_nome["rate"]["tipo"]
    assert metadados_por_nome["rate"]["estatisticas"]["media"] == pytest.approx(0.84, rel=1e-3)
    assert metadados_por_nome["carrier"]["estatisticas"] == {}
