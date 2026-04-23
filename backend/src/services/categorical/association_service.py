"""
Detector: Regra de Associação (Co-ocorrência de Pares)
Tipo: Categórico
Teoria: Para cada par de colunas (col_i, col_j), calcula a frequência de
        co-ocorrência de cada par de valores. Pares que raramente aparecem juntos
        recebem score alto. Detecta combinações anômalas que individualmente
        podem ser comuns mas juntas são raras.
        Exemplo: "cidade=São Paulo" e "estado=Minas Gerais" — cada valor é comum,
                 mas a combinação é improvável.
Gráfico sugerido: heatmap de co-ocorrência entre pares de categorias.
"""

import numpy as np
import pandas as pd
from itertools import combinations


DETECTOR_NAME = "assoc"
DETECTOR_LABEL = "Co-ocorrência de Pares"
DETECTOR_TYPE = "categorical"


def detect(df: pd.DataFrame, columns: list[str], contamination: float = 0.05) -> pd.DataFrame:
    """
    Parâmetros
    ----------
    df : DataFrame original
    columns : colunas categóricas a analisar (pares são formados entre elas)
    contamination : fração esperada de anomalias (define o percentil de corte)

    Retorna
    -------
    DataFrame com colunas adicionais:
        assoc_score   — soma dos log-probs de co-ocorrência de todos os pares da linha
        assoc_anomaly — 1 se score abaixo do percentil contamination
    """
    X = df[columns].copy().fillna("__missing__").astype(str)
    n = len(X)

    if len(columns) < 2:
        # não tem pares para analisar — fallback para frequência simples
        result = df.copy()
        result[f"{DETECTOR_NAME}_score"]   = 0.0
        result[f"{DETECTOR_NAME}_anomaly"] = 0
        return result

    log_probs = np.zeros(n)

    for col_a, col_b in combinations(columns, 2):
        pair = X[col_a] + "|||" + X[col_b]
        pair_freq = pair.value_counts(normalize=True)
        pair_probs = pair.map(pair_freq).fillna(1e-6).values
        log_probs += np.log(np.clip(pair_probs, 1e-9, 1.0))

    # normaliza pelo número de pares
    n_pairs = len(list(combinations(columns, 2)))
    log_probs /= n_pairs

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
        "chart": "heatmap_cooccurrence",
        "description": "Co-ocorrência de pares de categorias. Combinações raras = anomalia.",
    }
