"""
Detector: Entropia por Linha (Log-Probabilidade Conjunta)
Tipo: Categórico
Teoria: Para cada linha, calcula o log da probabilidade conjunta de todos os valores,
        assumindo independência entre colunas (modelo naive):
            log P(linha) = Σ log P(valor_col_i)
        Quanto mais negativo o log-prob, mais improvável é aquela combinação de categorias.
        Detecta linhas com combinações globalmente raras, mesmo que cada valor
        individualmente seja comum.
Gráfico sugerido: bar chart ou scatter de log-prob por linha, com threshold horizontal.
"""

import numpy as np
import pandas as pd


DETECTOR_NAME = "entropy"
DETECTOR_LABEL = "Entropia por Linha"
DETECTOR_TYPE = "categorical"


def detect(df: pd.DataFrame, columns: list[str], contamination: float = 0.05) -> pd.DataFrame:
    """
    Parâmetros
    ----------
    df : DataFrame original
    columns : colunas categóricas a analisar
    contamination : fração esperada de anomalias (define o percentil de corte)

    Retorna
    -------
    DataFrame com colunas adicionais:
        entropy_score   — log-probabilidade conjunta (mais negativo = mais anômalo)
        entropy_anomaly — 1 se score abaixo do percentil contamination
    """
    X = df[columns].copy().fillna("__missing__").astype(str)

    log_probs = np.zeros(len(X))

    for col in columns:
        freq_map = X[col].value_counts(normalize=True)
        col_probs = X[col].map(freq_map).fillna(1e-6).values
        log_probs += np.log(np.clip(col_probs, 1e-9, 1.0))

    # score mais negativo = combinação mais rara = mais anômala
    cutoff = np.percentile(log_probs, contamination * 100)

    result = df.copy()
    result[f"{DETECTOR_NAME}_score"]   = log_probs
    result[f"{DETECTOR_NAME}_anomaly"] = (log_probs <= cutoff).astype(int)

    return result


def score_info() -> dict:
    return {
        "name": DETECTOR_LABEL,
        "score_col": f"{DETECTOR_NAME}_score",
        "anomaly_col": f"{DETECTOR_NAME}_anomaly",
        "type": DETECTOR_TYPE,
        "chart": "bar_logprob",
        "description": "Log-probabilidade conjunta das categorias da linha. Combinações raras = anomalia.",
    }
