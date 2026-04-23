"""
Registry de detectores de anomalia.
Importa todos os services e expõe listas prontas para uso nas rotas.
"""

from .numeric import (
    zscore_service,
    iqr_service,
    mad_service,
    mahalanobis_service,
    knn_service,
    lof_service,
    iforest_service,
    percentile_service,
)
from .categorical import (
    frequency_service,
    entropy_service,
    chi2_service,
    binomial_service,
    association_service,
    lof_cat_service,
)

NUMERIC_DETECTORS = [
    zscore_service,
    iqr_service,
    mad_service,
    mahalanobis_service,
    knn_service,
    lof_service,
    iforest_service,
    percentile_service,
]

CATEGORICAL_DETECTORS = [
    frequency_service,
    entropy_service,
    chi2_service,
    binomial_service,
    association_service,
    lof_cat_service,
]

ALL_DETECTORS = NUMERIC_DETECTORS + CATEGORICAL_DETECTORS


def get_models_list() -> list[dict]:
    
    result = []
    for det in NUMERIC_DETECTORS:
        info = det.score_info()
        result.append({
            "id":   info["name"].lower().replace(" ", "_"),
            "nome": info["name"],
            "tipo": "numerico",
        })
    for det in CATEGORICAL_DETECTORS:
        info = det.score_info()
        result.append({
            "id":   info["name"].lower().replace(" ", "_"),
            "nome": info["name"],
            "tipo": "categorico",
        })
    return result


def run_selected(
    df,
    model_ids: list[str],
    numeric_cols: list[str],
    categorical_cols: list[str],
    contamination: float = 0.05,
):
    """
    Executa apenas os detectores selecionados pelo usuário.
    Retorna o DataFrame com todas as colunas de score e anomaly adicionadas,
    mais as colunas de consenso (anomaly_count, is_anomaly, anomaly_models).
    """
    import pandas as pd
    result = df.copy()
    flags = []

    id_to_detector = {
        det.score_info()["name"].lower().replace(" ", "_"): det
        for det in ALL_DETECTORS
    }

    for model_id in model_ids:
        det = id_to_detector.get(model_id)
        if det is None:
            continue

        info = det.score_info()
        cols = numeric_cols if info["type"] == "numeric" else categorical_cols

        if not cols:
            continue

        try:
            result = det.detect(result, cols, contamination)
            flags.append(info["anomaly_col"])
        except Exception as e:
            print(f"[WARN] {model_id} falhou: {e}")

    if flags:
        result["anomaly_count"]  = result[flags].sum(axis=1)
        result["is_anomaly"]     = (result["anomaly_count"] >= 1).astype(int)
        result["anomaly_models"] = result[flags].apply(
            lambda r: ",".join(f.replace("_anomaly", "") for f in flags if r[f] == 1),
            axis=1,
        )

    return result
