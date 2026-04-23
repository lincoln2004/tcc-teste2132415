"""
Detector: Modified Z-Score (MAD)
Tipo: Numérico
Teoria: Substitui média e desvio-padrão por mediana e MAD (Median Absolute Deviation).
        MAD = mediana(|xi - mediana(X)|).
        Score: 0.6745 * |xi - mediana| / MAD
        O fator 0.6745 normaliza para equivaler ao desvio-padrão em distribuições normais.
        Muito mais robusto que Z-Score clássico quando há outliers extremos puxando a média.
Gráfico sugerido: histograma com linhas nos limites ±threshold do MAD-score.
"""

import numpy as np
import pandas as pd


DETECTOR_NAME = "mad"
DETECTOR_LABEL = "Modified Z-Score (MAD)"
DETECTOR_TYPE = "numeric"

THRESHOLD = 3.5  # Iglewicz & Hoaglin (1993): threshold padrão para MAD-score


def detect(df: pd.DataFrame, columns: list[str], contamination: float = 0.05) -> pd.DataFrame:
    """
    Parâmetros
    ----------
    df : DataFrame original
    columns : colunas numéricas a analisar
    contamination : ajusta o threshold via percentil se o threshold fixo (3.5) for
                    muito conservador para o dataset

    Retorna
    -------
    DataFrame com colunas adicionais:
        mad_score   — maior modified z-score entre as colunas analisadas
        mad_anomaly — 1 se alguma coluna ultrapassou o threshold
    """
    X = df[columns].copy().fillna(df[columns].median())

    scores = pd.DataFrame(index=X.index)
    for col in columns:
        median = X[col].median()
        mad = (X[col] - median).abs().median()
        if mad == 0:
            # MAD zero: coluna constante ou quase — usa desvio padrão como fallback
            mad = X[col].std() or 1e-9
        scores[col] = 0.6745 * (X[col] - median).abs() / mad

    max_scores = scores.max(axis=1)

    # threshold: usa o fixo clássico, mas adapta pelo percentil se contamination forçar
    threshold = max(THRESHOLD, np.percentile(max_scores, (1 - contamination) * 100))

    result = df.copy()
    result[f"{DETECTOR_NAME}_score"] = max_scores
    result[f"{DETECTOR_NAME}_anomaly"] = (max_scores > threshold).astype(int)

    return result


def score_info() -> dict:
    return {
        "name": DETECTOR_LABEL,
        "score_col": f"{DETECTOR_NAME}_score",
        "anomaly_col": f"{DETECTOR_NAME}_anomaly",
        "type": DETECTOR_TYPE,
        "chart": "histogram_with_limits",
        "description": "Z-Score modificado via MAD. Robusto quando há outliers extremos.",
    }
