"""
Detector: KNN (K-Nearest Neighbors distance)
Tipo: Numérico
Teoria: Para cada ponto, calcula a distância média aos k vizinhos mais próximos.
        Pontos em regiões esparsas têm distância alta e são marcados como anomalias.
        Diferente do LOF, não normaliza pela densidade local — é uma medida absoluta.
Gráfico sugerido: scatter 2D (ou PCA se >2 features) com cor proporcional ao knn_score.
"""

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors


DETECTOR_NAME = "knn"
DETECTOR_LABEL = "KNN Distance"
DETECTOR_TYPE = "numeric"


def detect(df: pd.DataFrame, columns: list[str], contamination: float = 0.05, k: int | None = None) -> pd.DataFrame:
    """
    Parâmetros
    ----------
    df : DataFrame original
    columns : colunas numéricas a analisar
    contamination : fração esperada de anomalias (define o percentil de corte)
    k : número de vizinhos. Se None, usa heurística sqrt(n)

    Retorna
    -------
    DataFrame com colunas adicionais:
        knn_score   — distância média aos k vizinhos mais próximos
        knn_anomaly — 1 se score > percentil (1-contamination)
    """
    X = df[columns].copy().fillna(df[columns].median()).values.astype(float)

    n = len(X)
    if k is None:
        k = max(5, int(np.sqrt(n)))
    k = min(k, n - 1)  # k não pode ser maior que n-1

    nn = NearestNeighbors(n_neighbors=k + 1, metric="euclidean")  # +1 inclui o próprio ponto
    nn.fit(X)
    distances, _ = nn.kneighbors(X)

    # exclui distância 0 (o próprio ponto é sempre o vizinho mais próximo de si)
    knn_scores = distances[:, 1:].mean(axis=1)

    cutoff = np.percentile(knn_scores, (1 - contamination) * 100)

    result = df.copy()
    result[f"{DETECTOR_NAME}_score"] = knn_scores
    result[f"{DETECTOR_NAME}_anomaly"] = (knn_scores > cutoff).astype(int)

    return result


def score_info() -> dict:
    return {
        "name": DETECTOR_LABEL,
        "score_col": f"{DETECTOR_NAME}_score",
        "anomaly_col": f"{DETECTOR_NAME}_anomaly",
        "type": DETECTOR_TYPE,
        "chart": "scatter_colored_score",
        "description": "Distância média aos k vizinhos. Pontos isolados têm score alto.",
    }
