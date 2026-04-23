"""
Detector: LOF com Ordinal Encoding
Tipo: Categórico
Teoria: Aplica ordinal encoding nas colunas categóricas e executa o LOF
        no espaço encodado. Detecta linhas cujas combinações de categorias
        formam pontos isolados no espaço de encoding — ou seja, combinações
        que raramente aparecem juntas em termos de vizinhança no espaço ordinal.
        Funciona melhor quando as categorias têm ordem implícita (ex: nível de risco,
        faixa etária, grau de escolaridade).
Gráfico sugerido: scatter 2D do espaço encodado (PCA se >2 colunas) com cor pelo LOF score.
"""

import numpy as np
import pandas as pd
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import OrdinalEncoder


DETECTOR_NAME = "lof_cat"
DETECTOR_LABEL = "LOF Categórico"
DETECTOR_TYPE = "categorical"


def detect(df: pd.DataFrame, columns: list[str], contamination: float = 0.05) -> pd.DataFrame:
    """
    Parâmetros
    ----------
    df : DataFrame original
    columns : colunas categóricas a analisar
    contamination : fração esperada de anomalias

    Retorna
    -------
    DataFrame com colunas adicionais:
        lof_cat_score   — LOF score invertido (maior = mais anômalo)
        lof_cat_anomaly — 1 se flagado pelo LOF
    """
    X = df[columns].copy().fillna("__missing__").astype(str)

    enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    X_enc = enc.fit_transform(X)

    lof = LocalOutlierFactor(contamination=contamination, novelty=False)
    labels = lof.fit_predict(X_enc)
    scores = -lof.negative_outlier_factor_   # invertido: maior = mais anômalo

    result = df.copy()
    result[f"{DETECTOR_NAME}_score"]   = scores
    result[f"{DETECTOR_NAME}_anomaly"] = (labels == -1).astype(int)

    return result


def score_info() -> dict:
    return {
        "name": DETECTOR_LABEL,
        "score_col": f"{DETECTOR_NAME}_score",
        "anomaly_col": f"{DETECTOR_NAME}_anomaly",
        "type": DETECTOR_TYPE,
        "chart": "scatter_colored_score",
        "description": "LOF aplicado após ordinal encoding. Detecta combinações de categorias raras.",
    }
