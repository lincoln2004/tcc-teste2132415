"""
Detector: IQR (Tukey Fences)
Tipo: Numérico
Teoria: Usa o intervalo interquartílico (Q3 - Q1) para definir limites.
        Qualquer valor fora de [Q1 - 1.5*IQR, Q3 + 1.5*IQR] é anomalia.
        Robusto a assimetria e não assume normalidade.
Gráfico sugerido: boxplot por coluna — outliers aparecem como pontos isolados.
"""

import numpy as np
import pandas as pd


DETECTOR_NAME = "iqr"
DETECTOR_LABEL = "IQR (Tukey)"
DETECTOR_TYPE = "numeric"


def detect(df: pd.DataFrame, columns: list[str], contamination: float = 0.05) -> pd.DataFrame:
    """
    Parâmetros
    ----------
    df : DataFrame original
    columns : colunas numéricas a analisar
    contamination : não altera o método clássico (1.5×IQR), mas pode ser usado
                    para ajustar o multiplicador via _fence_multiplier()

    Retorna
    -------
    DataFrame com colunas adicionais:
        iqr_score   — distância máxima normalizada pelo IQR entre as colunas
        iqr_anomaly — 1 se alguma coluna está fora do fence, 0 caso contrário
    """
    X = df[columns].copy().fillna(df[columns].median())

    Q1 = X.quantile(0.25)
    Q3 = X.quantile(0.75)
    IQR = Q3 - Q1

    multiplier = _fence_multiplier(contamination)
    lower = Q1 - multiplier * IQR
    upper = Q3 + multiplier * IQR

    # distância normalizada fora do fence (0 se dentro)
    below = ((lower - X) / IQR.replace(0, np.nan)).clip(lower=0)
    above = ((X - upper) / IQR.replace(0, np.nan)).clip(lower=0)
    dist = (below + above).fillna(0)

    result = df.copy()
    result[f"{DETECTOR_NAME}_score"] = dist.max(axis=1)
    result[f"{DETECTOR_NAME}_anomaly"] = (
        ((X < lower) | (X > upper)).any(axis=1)
    ).astype(int)

    return result


def _fence_multiplier(contamination: float) -> float:
    """
    Tukey clássico usa 1.5. Para contamination menor (menos anomalias esperadas),
    aumenta o multiplicador tornando o critério mais conservador.
    """
    # mapeamento linear simples: 5% → 1.5, 1% → 2.5
    return max(1.5, 1.5 + (0.05 - contamination) * 20)


def score_info() -> dict:
    return {
        "name": DETECTOR_LABEL,
        "score_col": f"{DETECTOR_NAME}_score",
        "anomaly_col": f"{DETECTOR_NAME}_anomaly",
        "type": DETECTOR_TYPE,
        "chart": "boxplot",
        "description": "Intervalo interquartílico de Tukey. Robusto a distribuições assimétricas.",
    }
