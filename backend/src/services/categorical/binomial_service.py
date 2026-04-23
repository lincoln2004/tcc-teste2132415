"""
Detector: Teste Binomial por Célula
Tipo: Categórico
Teoria: Para cada (coluna, valor), testa se a frequência observada é estatisticamente
        improvável sob a hipótese nula de que cada categoria tem probabilidade uniforme
        de 1/k (k = número de categorias distintas na coluna).
        Usa o teste binomial exato: P(X <= observado | n, p_esperada)
        P-valor baixo = frequência observada muito menor que o esperado = valor raro.
Gráfico sugerido: heatmap de p-valores (linhas = amostras, colunas = features),
                  células vermelhas = p < alpha.
"""

import numpy as np
import pandas as pd
from scipy import stats


DETECTOR_NAME = "binomial"
DETECTOR_LABEL = "Teste Binomial"
DETECTOR_TYPE = "categorical"


def detect(df: pd.DataFrame, columns: list[str], contamination: float = 0.05) -> pd.DataFrame:
    """
    Parâmetros
    ----------
    df : DataFrame original
    columns : colunas categóricas a analisar
    contamination : alpha do teste por célula

    Retorna
    -------
    DataFrame com colunas adicionais:
        binomial_score        — menor p-valor entre as colunas da linha (mais baixo = mais anômalo)
        binomial_anomaly      — 1 se algum p-valor < contamination
        binomial_pval_<col>   — p-valor do valor da linha para cada coluna analisada
    """
    X = df[columns].copy().fillna("__missing__").astype(str)
    n = len(X)

    pval_cols = {}
    for col in columns:
        counts = X[col].value_counts()
        k = len(counts)
        p_uniform = 1.0 / k   # probabilidade esperada sob uniformidade

        # p-valor por valor: P(X <= count_observado | n, p_uniforme)
        pval_map = {}
        for val, count in counts.items():
            pval = stats.binom_test(count, n=n, p=p_uniform, alternative="less")
            pval_map[val] = pval

        col_pvals = X[col].map(pval_map).fillna(1.0).values
        pval_cols[f"{DETECTOR_NAME}_pval_{col}"] = col_pvals

    pval_df = pd.DataFrame(pval_cols, index=df.index)

    result = df.copy()
    for col_name, col_vals in pval_cols.items():
        result[col_name] = col_vals

    result[f"{DETECTOR_NAME}_score"]   = pval_df.min(axis=1)   # menor p-valor da linha
    result[f"{DETECTOR_NAME}_anomaly"] = (pval_df.min(axis=1) < contamination).astype(int)

    return result


def score_info() -> dict:
    return {
        "name": DETECTOR_LABEL,
        "score_col": f"{DETECTOR_NAME}_score",
        "anomaly_col": f"{DETECTOR_NAME}_anomaly",
        "type": DETECTOR_TYPE,
        "chart": "heatmap_pvalues",
        "description": "Teste binomial exato por célula. P-valor baixo = valor estatisticamente raro.",
    }
