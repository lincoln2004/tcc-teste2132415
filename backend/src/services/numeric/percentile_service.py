"""
Detector: Percentile Fence
Tipo: Numérico
Teoria: Valores abaixo do percentil (contamination/2) ou acima do percentil
        (1 - contamination/2) são anomalias. Método mais simples e direto,
        sem nenhuma suposição sobre a distribuição. Equivale a aparar as caudas
        da distribuição empírica.
Gráfico sugerido: CDF por coluna com faixas sombreadas nas regiões de corte.
"""

import numpy as np
import pandas as pd


DETECTOR_NAME = "percentile"
DETECTOR_LABEL = "Percentile Fence"
DETECTOR_TYPE = "numeric"


def detect(df: pd.DataFrame, columns: list[str], contamination: float = 0.05) -> pd.DataFrame:
    """
    Parâmetros
    ----------
    df : DataFrame original
    columns : colunas numéricas a analisar
    contamination : fração total de anomalias esperada (dividida igualmente entre caudas)

    Retorna
    -------
    DataFrame com colunas adicionais:
        percentile_score   — distância máxima normalizada ao fence mais próximo
        percentile_anomaly — 1 se alguma coluna está fora dos percentis de corte
    """
    X = df[columns].copy().fillna(df[columns].median())

    half = contamination / 2 * 100   # ex: 2.5 para contamination=0.05
    lower = X.quantile(half / 100)
    upper = X.quantile(1 - half / 100)

    below = (lower - X).clip(lower=0)
    above = (X - upper).clip(lower=0)
    ranges = (upper - lower).replace(0, np.nan)

    # score normalizado pelo range do fence
    dist = ((below + above) / ranges).fillna(0)

    result = df.copy()
    result[f"{DETECTOR_NAME}_score"] = dist.max(axis=1)
    result[f"{DETECTOR_NAME}_anomaly"] = (
        ((X < lower) | (X > upper)).any(axis=1)
    ).astype(int)

    return result


def score_info() -> dict:
    return {
        "name": DETECTOR_LABEL,
        "score_col": f"{DETECTOR_NAME}_score",
        "anomaly_col": f"{DETECTOR_NAME}_anomaly",
        "type": DETECTOR_TYPE,
        "chart": "cdf_with_fences",
        "description": "Corte direto nos percentis das caudas. Sem suposições de distribuição.",
    }
