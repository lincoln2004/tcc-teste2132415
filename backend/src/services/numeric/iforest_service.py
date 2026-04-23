"""
Detector: Isolation Forest
Tipo: Numérico
Teoria: Constrói árvores de decisão com cortes aleatórios nas features.
        Pontos anômalos são isolados mais rapidamente (árvores mais rasas)
        pois estão em regiões esparsas do espaço. O score é a profundidade
        média de isolamento normalizada.
        Sem suposição de distribuição. Eficiente para alta dimensão.
Gráfico sugerido: scatter com cor proporcional ao score + bar chart de feature importance.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


DETECTOR_NAME = "iforest"
DETECTOR_LABEL = "Isolation Forest"
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
        iforest_score        — anomaly score (maior = mais anômalo)
        iforest_anomaly      — 1 se flagado
        iforest_importance_* — contribuição por feature (uma coluna por feature)
    """
    X = df[columns].copy().fillna(df[columns].median())

    iso = IsolationForest(contamination=contamination, random_state=42)
    iso.fit(X)

    scores = -iso.score_samples(X)   # invertido: maior = mais anômalo
    labels = (iso.predict(X) == -1).astype(int)

    result = df.copy()
    result[f"{DETECTOR_NAME}_score"] = scores
    result[f"{DETECTOR_NAME}_anomaly"] = labels

    # feature importance aproximada: variância do score quando cada coluna é permutada
    for col in columns:
        X_perm = X.copy()
        X_perm[col] = np.random.permutation(X_perm[col].values)
        perm_scores = -iso.score_samples(X_perm)
        importance = np.abs(scores - perm_scores).mean()
        result[f"{DETECTOR_NAME}_importance_{col}"] = importance

    return result


def score_info() -> dict:
    return {
        "name": DETECTOR_LABEL,
        "score_col": f"{DETECTOR_NAME}_score",
        "anomaly_col": f"{DETECTOR_NAME}_anomaly",
        "type": DETECTOR_TYPE,
        "chart": "scatter_colored_score",
        "description": "Isolamento aleatório por árvores. Sem suposição de distribuição.",
    }
