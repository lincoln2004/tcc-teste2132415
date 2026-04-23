"""
Detector: Distância de Mahalanobis
Tipo: Numérico
Teoria: Generalização da distância euclidiana que considera a correlação entre variáveis
        e a escala de cada uma. Um ponto anômalo não precisa ser extremo em nenhuma coluna
        individualmente — basta ter uma combinação improvável entre elas.
        D²(x) = (x - μ)ᵀ Σ⁻¹ (x - μ)
        D² segue distribuição chi-quadrado com p graus de liberdade (p = nº de features).
        Threshold: percentil (1 - contamination) da chi-quadrado.
Gráfico sugerido: scatter de D² por índice de linha com linha horizontal no threshold.
"""

import numpy as np
import pandas as pd
from scipy import stats


DETECTOR_NAME = "mahalanobis"
DETECTOR_LABEL = "Mahalanobis"
DETECTOR_TYPE = "numeric"


def detect(df: pd.DataFrame, columns: list[str], contamination: float = 0.05) -> pd.DataFrame:
    """
    Parâmetros
    ----------
    df : DataFrame original
    columns : colunas numéricas a analisar (precisa de pelo menos 2)
    contamination : define o percentil chi-quadrado usado como threshold

    Retorna
    -------
    DataFrame com colunas adicionais:
        mahalanobis_score   — distância de Mahalanobis ao quadrado (D²)
        mahalanobis_anomaly — 1 se D² > threshold chi-quadrado
    """
    X = df[columns].copy().fillna(df[columns].median()).values.astype(float)

    mean = X.mean(axis=0)
    cov = np.cov(X, rowvar=False)

    try:
        cov_inv = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        # matriz singular: usa pseudoinversa
        cov_inv = np.linalg.pinv(cov)

    diff = X - mean
    d2 = np.array([d @ cov_inv @ d for d in diff])

    # threshold: percentil (1-contamination) da chi-quadrado com p graus de liberdade
    p = X.shape[1]
    threshold = stats.chi2.ppf(1 - contamination, df=p)

    result = df.copy()
    result[f"{DETECTOR_NAME}_score"] = d2
    result[f"{DETECTOR_NAME}_anomaly"] = (d2 > threshold).astype(int)

    return result


def score_info() -> dict:
    return {
        "name": DETECTOR_LABEL,
        "score_col": f"{DETECTOR_NAME}_score",
        "anomaly_col": f"{DETECTOR_NAME}_anomaly",
        "type": DETECTOR_TYPE,
        "chart": "scatter_score_line",
        "description": "Distância multivariada considerando correlação entre colunas.",
    }
