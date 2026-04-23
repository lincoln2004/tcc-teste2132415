"""
Detector: LOF (Local Outlier Factor)
Tipo: Numérico
Teoria: Compara a densidade local de um ponto com a densidade dos seus k vizinhos.
        LOF ≈ 1 → ponto tem densidade similar aos vizinhos (normal).
        LOF >> 1 → ponto está em região muito menos densa que seus vizinhos (anomalia).
        Detecta outliers contextuais: um ponto pode ser normal globalmente mas anômalo
        dentro do seu cluster local.
Gráfico sugerido: scatter com tamanho ou cor do ponto proporcional ao LOF score.
"""

import numpy as np
import pandas as pd
from sklearn.neighbors import LocalOutlierFactor


DETECTOR_NAME = "lof"
DETECTOR_LABEL = "LOF"
DETECTOR_TYPE = "numeric"


def detect(df: pd.DataFrame, columns: list[str], contamination: float = 0.05) -> pd.DataFrame:
    """
    Parâmetros
    ----------
    df : DataFrame original
    columns : colunas numéricas a analisar
    contamination : fração esperada de anomalias

    Retorna
    -------
    DataFrame com colunas adicionais:
        lof_score   — LOF score (invertido: maior = mais anômalo)
        lof_anomaly — 1 se flagado pelo LOF
    """
    X = df[columns].copy().fillna(df[columns].median()).values.astype(float)

    lof = LocalOutlierFactor(contamination=contamination, novelty=False)
    labels = lof.fit_predict(X)

    # negative_outlier_factor_ é negativo: quanto mais negativo, mais anômalo
    # invertemos para que score alto = mais anômalo (consistente com os outros detectores)
    scores = -lof.negative_outlier_factor_

    result = df.copy()
    result[f"{DETECTOR_NAME}_score"] = scores
    result[f"{DETECTOR_NAME}_anomaly"] = (labels == -1).astype(int)

    return result


def score_info() -> dict:
    return {
        "name": DETECTOR_LABEL,
        "score_col": f"{DETECTOR_NAME}_score",
        "anomaly_col": f"{DETECTOR_NAME}_anomaly",
        "type": DETECTOR_TYPE,
        "chart": "scatter_colored_score",
        "description": "Densidade local vs vizinhos. Detecta outliers contextuais.",
    }
