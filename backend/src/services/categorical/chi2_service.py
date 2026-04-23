"""
Detector: Chi-Quadrado por Coluna
Tipo: Categórico
Teoria: Para cada coluna, testa se a distribuição observada difere
        significativamente da distribuição uniforme esperada.
        Se a coluna for não uniforme (p < alpha), as linhas com valores
        cuja frequência é menor que o esperado são flagadas.
        Resíduo por célula: (observado - esperado) / sqrt(esperado)
        Resíduos altos negativos indicam categorias sistematicamente sub-representadas.
Gráfico sugerido: bar chart dos resíduos padronizados por categoria, com linha em ±2.
"""

import numpy as np
import pandas as pd
from scipy import stats


DETECTOR_NAME = "chi2"
DETECTOR_LABEL = "Chi-Quadrado"
DETECTOR_TYPE = "categorical"


def detect(df: pd.DataFrame, columns: list[str], contamination: float = 0.05) -> pd.DataFrame:
    """
    Parâmetros
    ----------
    df : DataFrame original
    columns : colunas categóricas a analisar
    contamination : alpha do teste (p < contamination → coluna é não uniforme)

    Retorna
    -------
    DataFrame com colunas adicionais:
        chi2_score        — soma dos resíduos negativos das colunas não uniformes
        chi2_anomaly      — 1 se a linha tem valores sub-representados em colunas significativas
        chi2_flagged_cols — colunas onde o valor da linha é estatisticamente raro
    """
    X = df[columns].copy().fillna("__missing__").astype(str)

    chi2_scores = np.zeros(len(X))
    flagged = [[] for _ in range(len(X))]

    for col in columns:
        counts = X[col].value_counts()
        n_cats = len(counts)
        if n_cats < 2:
            continue

        expected_count = len(X) / n_cats
        expected = np.full(n_cats, expected_count)
        _, p_value = stats.chisquare(counts.values, f_exp=expected)

        if p_value >= contamination:
            continue  # distribuição uniforme — coluna não contribui

        # resíduo padronizado por categoria
        residuals = (counts.values - expected) / np.sqrt(expected)
        residual_map = dict(zip(counts.index, residuals))

        col_residuals = X[col].map(residual_map).fillna(0).values

        # resíduo negativo = valor sub-representado (mais anômalo)
        chi2_scores += np.clip(-col_residuals, 0, None)

        threshold_res = -2.0  # resíduo < -2 é convencional para sub-representação
        for i, res in enumerate(col_residuals):
            if res < threshold_res:
                flagged[i].append(col)

    cutoff = np.percentile(chi2_scores, (1 - contamination) * 100)

    result = df.copy()
    result[f"{DETECTOR_NAME}_score"]        = chi2_scores
    result[f"{DETECTOR_NAME}_anomaly"]      = (chi2_scores >= cutoff).astype(int)
    result[f"{DETECTOR_NAME}_flagged_cols"] = [",".join(c) for c in flagged]

    return result


def score_info() -> dict:
    return {
        "name": DETECTOR_LABEL,
        "score_col": f"{DETECTOR_NAME}_score",
        "anomaly_col": f"{DETECTOR_NAME}_anomaly",
        "type": DETECTOR_TYPE,
        "chart": "bar_residuals",
        "description": "Resíduos do chi-quadrado. Valores sub-representados têm resíduo alto.",
    }
