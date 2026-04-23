"""
Detector: Z-Score
Tipo: Numérico
Teoria: Mede quantos desvios-padrão um valor está afastado da média da coluna.
        Valores com |z| > threshold são considerados anomalias.
        Assume distribuição aproximadamente normal.
Gráfico sugerido: histograma por coluna com linhas verticais nos limites ±threshold.
"""

import numpy as np
import pandas as pd
from scipy import stats


DETECTOR_NAME = "zscore"
DETECTOR_LABEL = "Z-Score"
DETECTOR_TYPE = "numeric"


def detect(df: pd.DataFrame, columns: list[str], contamination: float = 0.05) -> pd.DataFrame:
    """
    Parâmetros
    ----------
    df : DataFrame original
    columns : colunas numéricas a analisar
    contamination : fração esperada de anomalias (define o threshold via ppf)

    Retorna
    -------
    DataFrame com colunas adicionais:
        zscore_score   — maior z-score absoluto entre as colunas analisadas
        zscore_anomaly — 1 se alguma coluna ultrapassou o threshold, 0 caso contrário
    """
    X = df[columns].copy().fillna(df[columns].median())

    z = np.abs(stats.zscore(X, nan_policy="omit"))

    # threshold estatístico: valor z que deixa contamination/2 em cada cauda
    threshold = stats.norm.ppf(1 - contamination / 2)

    result = df.copy()
    result[f"{DETECTOR_NAME}_score"] = pd.DataFrame(z, columns=columns).max(axis=1)
    result[f"{DETECTOR_NAME}_anomaly"] = (
        pd.DataFrame(z, columns=columns).max(axis=1) > threshold
    ).astype(int)

    return result


def score_info() -> dict:
    return {
        "name": DETECTOR_LABEL,
        "score_col": f"{DETECTOR_NAME}_score",
        "anomaly_col": f"{DETECTOR_NAME}_anomaly",
        "type": DETECTOR_TYPE,
        "chart": "histogram_with_limits",
        "description": "Distância em desvios-padrão da média por coluna.",
    }
