"""
Detector: Frequência Relativa
Tipo: Categórico
Teoria: Para cada coluna, calcula a frequência relativa de cada valor.
        Uma linha é anômala se a média das frequências dos seus valores
        estiver abaixo do threshold definido pelo contamination.
        É o método mais intuitivo e explicável: simplesmente, valores raros = anomalia.
Gráfico sugerido: bar chart de contagem por categoria, com barras abaixo do threshold em vermelho.
"""

import numpy as np
import pandas as pd


DETECTOR_NAME = "freq"
DETECTOR_LABEL = "Frequência Relativa"
DETECTOR_TYPE = "categorical"


def detect(df: pd.DataFrame, columns: list[str], contamination: float = 0.05) -> pd.DataFrame:
    """
    Parâmetros
    ----------
    df : DataFrame original
    columns : colunas categóricas a analisar
    contamination : fração esperada de anomalias (define o percentil de corte do score)

    Retorna
    -------
    DataFrame com colunas adicionais:
        freq_score        — média das frequências relativas dos valores da linha
        freq_anomaly      — 1 se score abaixo do percentil contamination
        freq_rare_cols    — lista das colunas onde o valor é raro (separadas por vírgula)
    """
    X = df[columns].copy().fillna("__missing__").astype(str)

    freq_scores = np.zeros(len(X))
    rare_cols = [[] for _ in range(len(X))]

    for col in columns:
        freq_map = X[col].value_counts(normalize=True)
        col_freq = X[col].map(freq_map).fillna(0).values
        freq_scores += col_freq

        col_threshold = np.percentile(col_freq, contamination * 100)
        for i, f in enumerate(col_freq):
            if f <= col_threshold:
                rare_cols[i].append(col)

    freq_scores /= len(columns)
    cutoff = np.percentile(freq_scores, contamination * 100)

    result = df.copy()
    result[f"{DETECTOR_NAME}_score"]     = freq_scores
    result[f"{DETECTOR_NAME}_anomaly"]   = (freq_scores <= cutoff).astype(int)
    result[f"{DETECTOR_NAME}_rare_cols"] = [",".join(c) for c in rare_cols]

    return result


def score_info() -> dict:
    return {
        "name": DETECTOR_LABEL,
        "score_col": f"{DETECTOR_NAME}_score",
        "anomaly_col": f"{DETECTOR_NAME}_anomaly",
        "type": DETECTOR_TYPE,
        "chart": "bar_frequency",
        "description": "Valores com frequência abaixo do threshold são raros.",
    }
