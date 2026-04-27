"""
Script de Benchmark para Detecção de Anomalias — Modelos Categóricos
=====================================================================

Avalia os detectores categóricos sobre datasets do ADBench, utilizando:
  - Colunas categóricas NATIVAS quando disponíveis (ex: valores inteiros com poucos níveis)
  - Discretização (binning) apenas para colunas numéricas densas

Modelos avaliados:
  - Frequência Relativa (freq)
  - Entropia por Linha (entropy)
  - Co-ocorrência de Pares (assoc)
  - Teste Binomial (binomial)
  - Chi-Quadrado (chi2)
  - LOF Categórico (lof_cat)

Uso: python benchmark_categorical_models_test.py
"""

import numpy as np
import pandas as pd
import time
import os
import sys
from datetime import datetime
from sklearn.metrics import (
    f1_score, precision_score, recall_score,
    roc_auc_score, average_precision_score,
    confusion_matrix
)
import warnings
warnings.filterwarnings("ignore")

# ============================================================================
# IMPORTAÇÃO DOS DETECTORES
# ============================================================================

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.categorical.frequency_service   import detect as freq_detect
from services.categorical.entropy_service     import detect as entropy_detect
from services.categorical.association_service import detect as assoc_detect
from services.categorical.binomial_service    import detect as binomial_detect
from services.categorical.chi2_service        import detect as chi2_detect
from services.categorical.lof_cat_service     import detect as lof_cat_detect


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Limite para considerar uma coluna numérica como "potencialmente categórica"
# Se uma coluna numérica tem <= MAX_UNIQUE_VALUES valores únicos, tratamos como categórica
MAX_UNIQUE_VALUES_CATEGORICAL = 10

# Bins para discretização de colunas numéricas densas
N_BINS = 5
BIN_LABELS = ["muito_baixo", "baixo", "medio", "alto", "muito_alto"]

# Lista de datasets conhecidos que têm colunas categóricas naturais
DATASETS_WITH_NATURAL_CATEGORICAL = {
    "cardio": {"cat_cols": [1, 2, 3], "description": "tipo de anomalia cardíaca"},
    "wine": {"cat_cols": [0], "description": "tipo de vinho (3 classes)"},
    "thyroid": {"cat_cols": [0, 1, 2], "description": "categorias de diagnóstico"},
    "annthyroid": {"cat_cols": [0], "description": "diagnóstico binário"},
}


# ============================================================================
# PALETA VISUAL
# ============================================================================

DARK_BG      = "#0D1B2A"
ACCENT_GREEN = "#05CB9D"
ACCENT_BLUE  = "#1A73E8"
LIGHT_GRAY   = "#F5F7FA"
MID_GRAY     = "#E0E4EA"
TEXT_DARK    = "#1C2B3A"
TEXT_MUTED   = "#6B7A8D"
WHITE        = "#FFFFFF"
RED_SOFT     = "#FF6B6B"
YELLOW_SOFT  = "#FFD166"
GREEN_SOFT   = "#06D6A0"
PURPLE_SOFT  = "#9B5DE5"

MODELS = {
    "freq":     {"detect": freq_detect,     "name": "Frequência Relativa"},
    "entropy":  {"detect": entropy_detect,  "name": "Entropia por Linha"},
    "assoc":    {"detect": assoc_detect,    "name": "Co-ocorrência de Pares"},
    "binomial": {"detect": binomial_detect, "name": "Teste Binomial"},
    "chi2":     {"detect": chi2_detect,     "name": "Chi-Quadrado"},
    "lof_cat":  {"detect": lof_cat_detect,  "name": "LOF Categórico"},
}


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def carregar_dataset(caminho: str):
    """Carrega dataset .npz do ADBench."""
    data = np.load(caminho, allow_pickle=True)
    X, y = data["X"], data["y"]
    colunas = [f"feature_{i}" for i in range(X.shape[1])]
    df = pd.DataFrame(X, columns=colunas)
    return df, y.astype(int)


def identificar_colunas_categoricas(df: pd.DataFrame, dataset_name: str = None) -> tuple:
    """
    Identifica colunas que podem ser tratadas como categóricas.
    
    Estratégia:
    1. Colunas do tipo object/category já são categóricas
    2. Colunas inteiras com poucos valores únicos (<= MAX_UNIQUE_VALUES_CATEGORICAL)
    3. Colunas conhecidas via mapeamento manual
    
    Retorna:
        df_cat: DataFrame com colunas convertidas para string
        colunas_categoricas: lista de nomes das colunas categóricas
        info: dicionário com estatísticas da conversão
    """
    df_cat = df.copy()
    colunas_categoricas = []
    info = {"nativas": [], "potencialmente_categoricas": [], "discretizadas": []}
    
    # 1. Colunas já categóricas (object ou category)
    for col in df.columns:
        if df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(df[col]):
            colunas_categoricas.append(col)
            info["nativas"].append(col)
            df_cat[col] = df[col].astype(str)
    
    # 2. Colunas numéricas com poucos valores únicos (potencialmente categóricas)
    for col in df.columns:
        if col in colunas_categoricas:
            continue
            
        nunique = df[col].nunique()
        if nunique <= MAX_UNIQUE_VALUES_CATEGORICAL and nunique > 1:
            colunas_categoricas.append(col)
            info["potencialmente_categoricas"].append(col)
            df_cat[col] = df[col].astype(str)
    
    # 3. Colunas numéricas densas -> discretizar em bins
    colunas_para_discretizar = [col for col in df.columns if col not in colunas_categoricas]
    
    for col in colunas_para_discretizar:
        vals = df[col].dropna()
        n_unique = vals.nunique()
        
        if n_unique < 2:
            continue  # constante, descarta
            
        bins = min(N_BINS, n_unique)
        labels = BIN_LABELS[:bins] if bins <= len(BIN_LABELS) else [str(i) for i in range(bins)]
        
        try:
            df_cat[col] = pd.qcut(df[col], q=bins, labels=labels, duplicates="drop").astype(str)
            colunas_categoricas.append(col)
            info["discretizadas"].append(col)
        except Exception:
            try:
                df_cat[col] = pd.cut(df[col], bins=bins, labels=labels[:bins], duplicates="drop").astype(str)
                colunas_categoricas.append(col)
                info["discretizadas"].append(col)
            except Exception:
                pass  # coluna problemática, descarta
    
    return df_cat, colunas_categoricas, info


def avaliar_modelo(y_true, y_pred, y_scores=None):
    """Calcula métricas de avaliação."""
    metrics = {
        "f1":        f1_score(y_true, y_pred, zero_division=0),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall":    recall_score(y_true, y_pred, zero_division=0),
    }
    if y_scores is not None:
        try:
            metrics["auc_roc"]       = roc_auc_score(y_true, y_scores)
            metrics["avg_precision"] = average_precision_score(y_true, y_scores)
        except Exception:
            metrics["auc_roc"] = metrics["avg_precision"] = np.nan
    else:
        metrics["auc_roc"] = metrics["avg_precision"] = np.nan

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    metrics.update({
        "true_positives":  int(tp),
        "false_positives": int(fp),
        "true_negatives":  int(tn),
        "false_negatives": int(fn),
        "specificity":     tn / (tn + fp) if (tn + fp) > 0 else np.nan,
    })
    return metrics


def _score_col(model_id: str, result_df: pd.DataFrame):
    """Retorna a coluna de score do modelo, tratando variações de nome."""
    candidate = f"{model_id}_score"
    if candidate in result_df.columns:
        return result_df[candidate].values
    return None


def _anomaly_col(model_id: str, result_df: pd.DataFrame):
    """Retorna a coluna de anomalia do modelo."""
    candidate = f"{model_id}_anomaly"
    if candidate in result_df.columns:
        return result_df[candidate].values
    raise KeyError(f"Coluna '{candidate}' não encontrada no resultado.")


# ============================================================================
# GERAÇÃO DO PDF
# ============================================================================

def _hex(color: str):
    from reportlab.lib import colors as rl_colors
    return rl_colors.HexColor(color)


def _score_color(value: float):
    if np.isnan(value):
        return _hex(TEXT_MUTED)
    if value >= 0.7:
        return _hex(GREEN_SOFT)
    if value >= 0.4:
        return _hex(YELLOW_SOFT)
    return _hex(RED_SOFT)


def gerar_pdf_resultados(results_df: pd.DataFrame, output_path: str):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.graphics.shapes import Drawing, Rect, String

    PAGE = landscape(A4)
    W, H = PAGE

    doc = SimpleDocTemplate(
        output_path,
        pagesize=PAGE,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.8*cm,  bottomMargin=1.8*cm,
    )

    styles = getSampleStyleSheet()

    def PS(name, **kw):
        return ParagraphStyle(name, parent=styles["Normal"], **kw)

    S_TITLE    = PS("T", fontSize=22, textColor=_hex(WHITE), alignment=TA_CENTER,
                    fontName="Helvetica-Bold", leading=28)
    S_SUBTITLE = PS("ST", fontSize=10, textColor=_hex(ACCENT_GREEN), alignment=TA_CENTER)
    S_CAPTION  = PS("CAP", fontSize=8, textColor=_hex(TEXT_MUTED), alignment=TA_CENTER)
    S_SECTION  = PS("SEC", fontSize=13, textColor=_hex(DARK_BG), fontName="Helvetica-Bold",
                    spaceBefore=14, spaceAfter=6)
    S_LABEL    = PS("LBL", fontSize=7, textColor=_hex(TEXT_MUTED), alignment=TA_CENTER)
    S_NOTE     = PS("NOTE", fontSize=7, textColor=_hex(TEXT_MUTED), leading=10)

    def hr(color=MID_GRAY, thickness=0.5):
        return HRFlowable(width="100%", thickness=thickness,
                          color=_hex(color), spaceAfter=6, spaceBefore=6)

    story = []

    # =========================================================================
    # CAPA
    # =========================================================================
    capa = Table(
        [[Paragraph("Benchmark de Detecção de Anomalias — Modelos Categóricos", S_TITLE)],
         [Paragraph(
             f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}  ·  "
             f"{len(results_df['modelo'].unique())} modelos  ·  "
             f"{len(results_df['dataset'].unique())} datasets  ·  "
             f"Limiar catégorias: {MAX_UNIQUE_VALUES_CATEGORICAL} valores únicos",
             S_SUBTITLE,
         )]],
        colWidths=None,
    )
    capa.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), _hex(DARK_BG)),
        ("TOPPADDING",    (0,0), (-1,-1), 18),
        ("BOTTOMPADDING", (0,0), (-1,-1), 18),
        ("LEFTPADDING",   (0,0), (-1,-1), 12),
        ("RIGHTPADDING",  (0,0), (-1,-1), 12),
    ]))
    story.append(capa)
    story.append(Spacer(1, 0.5*cm))

    # Nota metodológica
    nota = Table(
        [[Paragraph(
            f"⚙️  Metodologia: identificação automática de colunas categóricas.\n"
            f"   • Colunas nativas: já eram categóricas\n"
            f"   • Colunas potencialmente categóricas: ≤ {MAX_UNIQUE_VALUES_CATEGORICAL} valores únicos\n"
            f"   • Colunas densas: discretizadas em {N_BINS} bins ('{', '.join(BIN_LABELS)}')",
            S_NOTE,
        )]],
        colWidths=None,
    )
    nota.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), _hex("#FFF8E1")),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LINEBELOW",     (0,0), (-1,-1), 1.5, _hex(YELLOW_SOFT)),
    ]))
    story.append(nota)
    story.append(Spacer(1, 0.4*cm))

    # KPIs
    rank_df = results_df.groupby("modelo").agg(
        f1=("f1","mean"), auc_roc=("auc_roc","mean"),
        tempo=("tempo_segundos","mean"),
    ).sort_values("f1", ascending=False).reset_index()

    best_model = MODELS.get(rank_df.iloc[0]["modelo"], {}).get("name", rank_df.iloc[0]["modelo"])
    best_f1    = rank_df.iloc[0]["f1"]
    avg_auc    = results_df["auc_roc"].mean()
    avg_time   = results_df["tempo_segundos"].mean()

    def kpi_card(title, value, sub=""):
        inner = Table(
            [[Paragraph(title, S_LABEL)],
             [Paragraph(value, PS("KV", fontSize=15, fontName="Helvetica-Bold",
                                  textColor=_hex(PURPLE_SOFT), alignment=TA_CENTER))],
             [Paragraph(sub, S_CAPTION)]],
            colWidths=None,
        )
        inner.setStyle(TableStyle([
            ("ALIGN",        (0,0), (-1,-1), "CENTER"),
            ("BACKGROUND",   (0,0), (-1,-1), _hex(LIGHT_GRAY)),
            ("TOPPADDING",   (0,0), (-1,-1), 10),
            ("BOTTOMPADDING",(0,0), (-1,-1), 10),
            ("LINEBELOW",    (0,0), (-1,0), 2, _hex(PURPLE_SOFT)),
        ]))
        return inner

    kpis = Table([[
        kpi_card("Melhor Modelo",  best_model, f"F1 médio: {best_f1:.4f}"),
        kpi_card("AUC-ROC Médio",  f"{avg_auc:.4f}", "Todos modelos/datasets"),
        kpi_card("Tempo Médio",    f"{avg_time:.2f}s", "Por execução"),
        kpi_card("Datasets",       str(len(results_df['dataset'].unique())), "Avaliados"),
    ]], colWidths=None, hAlign="CENTER")
    kpis.setStyle(TableStyle([("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6)]))
    story.append(kpis)
    story.append(Spacer(1, 0.4*cm))
    story.append(hr(PURPLE_SOFT, thickness=1.5))

    # =========================================================================
    # SEÇÃO 1 — RANKING
    # =========================================================================
    story.append(Paragraph("1. Ranking dos Modelos Categóricos (F1-Score Médio)", S_SECTION))

    max_f1 = rank_df["f1"].max() if rank_df["f1"].max() > 0 else 1

    def bar_cell(value, max_val, width_pts=110, color=PURPLE_SOFT):
        d = Drawing(width_pts, 14)
        bar_w = max(2, int((value / max_val) * (width_pts - 4)))
        d.add(Rect(0, 3, width_pts - 4, 8, fillColor=_hex(MID_GRAY), strokeColor=None))
        d.add(Rect(0, 3, bar_w, 8, fillColor=_hex(color), strokeColor=None))
        d.add(String(width_pts - 2, 4, f"{value:.4f}",
                     fontSize=7, fillColor=_hex(TEXT_DARK), textAnchor="end"))
        return d

    rank_header = [["#", "Modelo", "F1-Score", "Precision", "Recall",
                    "AUC-ROC", "Avg Prec", "Tempo (s)"]]
    rank_rows = []
    for i, row in rank_df.iterrows():
        full_rank = results_df.groupby("modelo").agg(
            precision=("precision","mean"), recall=("recall","mean"),
            avg_precision=("avg_precision","mean"),
        ).loc[row["modelo"]]

        rank_rows.append([
            str(i + 1),
            MODELS.get(row["modelo"], {}).get("name", row["modelo"]),
            bar_cell(row["f1"], max_f1, color=PURPLE_SOFT),
            f"{full_rank['precision']:.4f}",
            f"{full_rank['recall']:.4f}",
            f"{row['auc_roc']:.4f}" if not np.isnan(row["auc_roc"]) else "—",
            f"{full_rank['avg_precision']:.4f}" if not np.isnan(full_rank["avg_precision"]) else "—",
            f"{row['tempo']:.2f}s",
        ])

    rank_table = Table(
        rank_header + rank_rows,
        colWidths=None,
        repeatRows=1,
    )
    rank_style = TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), _hex(DARK_BG)),
        ("TEXTCOLOR",     (0,0), (-1,0), _hex(WHITE)),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0), 8),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("FONTSIZE",      (0,1), (-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("GRID",          (0,0), (-1,-1), 0.3, _hex(MID_GRAY)),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [_hex(WHITE), _hex(LIGHT_GRAY)]),
        ("BACKGROUND",    (0,1), (-1,1), _hex("#F0EAFF")),
        ("FONTNAME",      (0,1), (-1,1), "Helvetica-Bold"),
        ("TEXTCOLOR",     (0,1), (0,1), _hex(PURPLE_SOFT)),
    ])
    rank_table.setStyle(rank_style)
    story.append(rank_table)
    story.append(Spacer(1, 0.4*cm))

    # =========================================================================
    # SEÇÃO 2 — ESTATÍSTICAS GERAIS
    # =========================================================================
    story.append(hr())
    story.append(Paragraph("2. Estatísticas Gerais", S_SECTION))

    stat_metrics = [
        ("F1-Score",      "f1"),
        ("Precision",     "precision"),
        ("Recall",        "recall"),
        ("AUC-ROC",       "auc_roc"),
        ("Avg Precision", "avg_precision"),
        ("Tempo (s)",     "tempo_segundos"),
    ]

    stat_header = [["Métrica", "Média", "Mediana", "Mínimo", "Máximo", "Desvio Padrão"]]
    stat_rows = []
    for label, col in stat_metrics:
        s = results_df[col].dropna()
        if len(s) == 0:
            stat_rows.append([label, "—","—","—","—","—"])
            continue
        stat_rows.append([
            label,
            f"{s.mean():.4f}", f"{s.median():.4f}",
            f"{s.min():.4f}", f"{s.max():.4f}", f"{s.std():.4f}",
        ])

    stat_table = Table(
        stat_header + stat_rows,
        colWidths=None,
    )
    stat_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), _hex(DARK_BG)),
        ("TEXTCOLOR",     (0,0), (-1,0), _hex(WHITE)),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0), 8),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("FONTSIZE",      (0,1), (-1,-1), 8),
        ("GRID",          (0,0), (-1,-1), 0.3, _hex(MID_GRAY)),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [_hex(WHITE), _hex(LIGHT_GRAY)]),
    ]))
    story.append(stat_table)

    # =========================================================================
    # SEÇÃO 3 — DETALHADO POR MODELO
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("3. Resultados Detalhados por Modelo", S_SECTION))
    story.append(hr())

    for modelo_id in rank_df["modelo"]:
        nome = MODELS.get(modelo_id, {}).get("name", modelo_id)
        mdf  = results_df[results_df["modelo"] == modelo_id].copy()

        mean_f1  = mdf["f1"].mean()
        mean_auc = mdf["auc_roc"].mean()

        m_header = Table(
            [[Paragraph(f"▶  {nome}", PS("MH", fontSize=10, fontName="Helvetica-Bold",
                                          textColor=_hex(DARK_BG))),
              Paragraph(f"F1 médio: {mean_f1:.4f}   AUC médio: {mean_auc:.4f}",
                        PS("MHS", fontSize=8, textColor=_hex(PURPLE_SOFT), alignment=TA_RIGHT))]],
            colWidths=None,
        )
        m_header.setStyle(TableStyle([
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
            ("RIGHTPADDING",  (0,0), (-1,-1), 10),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))

        dh = [["Dataset", "F1", "Precision", "Recall", "AUC-ROC",
               "Avg Prec", "Tempo(s)", "TP", "FP", "FN", "TN",
               "Colunas Cat.", "Tipo Colunas"]]
        dr = []
        for _, row in mdf.sort_values("f1", ascending=False).iterrows():
            n_cat = row.get("n_cat_cols", "—")
            tipo_cols = row.get("tipo_colunas", "—")
            dr.append([
                row["dataset"],
                f"{row['f1']:.4f}",
                f"{row['precision']:.4f}",
                f"{row['recall']:.4f}",
                f"{row['auc_roc']:.4f}" if not np.isnan(row["auc_roc"]) else "—",
                f"{row['avg_precision']:.4f}" if not np.isnan(row.get("avg_precision", np.nan)) else "—",
                f"{row['tempo_segundos']:.2f}s",
                str(row["true_positives"]),
                str(row["false_positives"]),
                str(row["false_negatives"]),
                str(row["true_negatives"]),
                str(n_cat),
                str(tipo_cols),
            ])
        dr.append([
            "── MÉDIA ──",
            f"{mdf['f1'].mean():.4f}",
            f"{mdf['precision'].mean():.4f}",
            f"{mdf['recall'].mean():.4f}",
            f"{mdf['auc_roc'].mean():.4f}",
            f"{mdf['avg_precision'].mean():.4f}" if "avg_precision" in mdf else "—",
            f"{mdf['tempo_segundos'].mean():.2f}s",
            str(int(mdf['true_positives'].sum())),
            str(int(mdf['false_positives'].sum())),
            str(int(mdf['false_negatives'].sum())),
            str(int(mdf['true_negatives'].sum())),
            "—",
            "—",
        ])

        detail_table = Table(
            dh + dr,
            colWidths=None,
            repeatRows=1,
        )
        dstyle = [
            ("BACKGROUND",    (0,0), (-1,0), _hex(DARK_BG)),
            ("TEXTCOLOR",     (0,0), (-1,0), _hex(WHITE)),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0), 7),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
            ("FONTSIZE",      (0,1), (-1,-1), 7),
            ("GRID",          (0,0), (-1,-1), 0.3, _hex(MID_GRAY)),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("ROWBACKGROUNDS",(0,1), (-1,-2), [_hex(WHITE), _hex(LIGHT_GRAY)]),
            ("BACKGROUND",    (0,-1), (-1,-1), _hex("#F0EAFF")),
            ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
        ]
        for row_i, (_, row) in enumerate(
            mdf.sort_values("f1", ascending=False).iterrows(), start=1
        ):
            color = _score_color(row["f1"])
            dstyle.append(("TEXTCOLOR", (1, row_i), (1, row_i), color))
            dstyle.append(("FONTNAME",  (1, row_i), (1, row_i), "Helvetica-Bold"))

        detail_table.setStyle(TableStyle(dstyle))
        story.append(KeepTogether([m_header, detail_table, Spacer(1, 0.4*cm)]))

    # =========================================================================
    # SEÇÃO 4 — MELHOR MODELO POR DATASET
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("4. Melhor Modelo por Dataset", S_SECTION))
    story.append(hr())

    best_ds = (results_df.loc[results_df.groupby("dataset")["f1"].idxmax()]
               .sort_values("dataset"))

    ds_header = [["Dataset", "Melhor Modelo", "F1", "Precision", "Recall",
                  "AUC-ROC", "Tempo (s)", "Colunas Cat.", "Tipo Colunas"]]
    ds_rows = []
    for _, row in best_ds.iterrows():
        ds_rows.append([
            row["dataset"],
            MODELS.get(row["modelo"], {}).get("name", row["modelo"]),
            f"{row['f1']:.4f}",
            f"{row['precision']:.4f}",
            f"{row['recall']:.4f}",
            f"{row['auc_roc']:.4f}" if not np.isnan(row["auc_roc"]) else "—",
            f"{row['tempo_segundos']:.2f}s",
            str(row.get("n_cat_cols", "—")),
            str(row.get("tipo_colunas", "—")),
        ])

    ds_table = Table(
        ds_header + ds_rows,
        colWidths=None,
    )
    ds_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), _hex(DARK_BG)),
        ("TEXTCOLOR",     (0,0), (-1,0), _hex(WHITE)),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0), 8),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("FONTSIZE",      (0,1), (-1,-1), 8),
        ("GRID",          (0,0), (-1,-1), 0.3, _hex(MID_GRAY)),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [_hex(WHITE), _hex(LIGHT_GRAY)]),
    ]))
    story.append(ds_table)
    story.append(Spacer(1, 0.6*cm))

    # =========================================================================
    # SEÇÃO 5 — MATRIZ DE CONFUSÃO ACUMULADA
    # =========================================================================
    story.append(Paragraph("5. Matriz de Confusão Acumulada por Modelo", S_SECTION))
    story.append(hr())

    cm_header = [["Modelo", "TP", "FP", "TN", "FN",
                  "Especificidade", "Recall", "F1 Médio"]]
    cm_rows = []
    for modelo_id in rank_df["modelo"]:
        nome = MODELS.get(modelo_id, {}).get("name", modelo_id)
        mdf  = results_df[results_df["modelo"] == modelo_id]
        tp = mdf["true_positives"].sum()
        fp = mdf["false_positives"].sum()
        tn = mdf["true_negatives"].sum()
        fn = mdf["false_negatives"].sum()
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0
        cm_rows.append([
            nome, str(tp), str(fp), str(tn), str(fn),
            f"{spec:.4f}", f"{rec:.4f}", f"{mdf['f1'].mean():.4f}",
        ])

    cm_table = Table(
        cm_header + cm_rows,
        colWidths=None,
    )
    cm_style = [
        ("BACKGROUND",    (0,0), (-1,0), _hex(DARK_BG)),
        ("TEXTCOLOR",     (0,0), (-1,0), _hex(WHITE)),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0), 8),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("FONTSIZE",      (0,1), (-1,-1), 8),
        ("GRID",          (0,0), (-1,-1), 0.3, _hex(MID_GRAY)),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [_hex(WHITE), _hex(LIGHT_GRAY)]),
    ]
    for i in range(1, len(cm_rows)+1):
        cm_style.append(("TEXTCOLOR", (1,i), (1,i), _hex(GREEN_SOFT)))
        cm_style.append(("FONTNAME",  (1,i), (1,i), "Helvetica-Bold"))
        cm_style.append(("TEXTCOLOR", (2,i), (2,i), _hex(RED_SOFT)))
    cm_table.setStyle(TableStyle(cm_style))
    story.append(cm_table)

    # Rodapé
    story.append(Spacer(1, 0.8*cm))
    story.append(hr(MID_GRAY))
    story.append(Paragraph(
        f"Relatório gerado automaticamente · {len(results_df)} execuções · "
        f"Limiar categórico: {MAX_UNIQUE_VALUES_CATEGORICAL} valores únicos · "
        f"Datasets: {', '.join(results_df['dataset'].unique())}",
        S_CAPTION,
    ))

    doc.build(story)
    print(f"✅ PDF gerado: {output_path}")


# ============================================================================
# EXECUÇÃO DO BENCHMARK
# ============================================================================

def executar_benchmark(datasets: list, output_dir: str = "benchmark_results",
                       max_cat_cols: int = 20):
    """
    Executa benchmark categórico.
    
    Parâmetros
    ----------
    datasets     : lista de (caminho, nome, contaminação)
    output_dir   : diretório para CSV e PDF
    max_cat_cols : máximo de colunas a usar (evita explosão combinatória no assoc)
    """
    os.makedirs(output_dir, exist_ok=True)
    all_results = []

    print("=" * 70)
    print("BENCHMARK — MODELOS CATEGÓRICOS")
    print(f"Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modelos: {len(MODELS)}  |  Datasets: {len(datasets)}")
    print(f"Limiar categórico: {MAX_UNIQUE_VALUES_CATEGORICAL} valores únicos")
    print("=" * 70)

    for dataset_path, dataset_name, true_contamination in datasets:
        print(f"\n📊 {dataset_name}  (contaminação: {true_contamination:.2%})")

        try:
            df_num, y_true = carregar_dataset(dataset_path)
            print(f"   Shape original: {df_num.shape}  |  Anomalias: {y_true.sum()} ({y_true.mean():.2%})")
        except Exception as e:
            print(f"   ❌ Erro ao carregar: {e}")
            continue

        # Identifica colunas categóricas (nativas + potencialmente categóricas + discretizadas)
        df_cat, cat_cols, info = identificar_colunas_categoricas(df_num, dataset_name)

        if len(cat_cols) < 2:
            print(f"   ⚠️  Apenas {len(cat_cols)} coluna categórica. Pulando...")
            continue

        # Limita colunas para evitar explosão no assoc (O(n²) pares)
        if len(cat_cols) > max_cat_cols:
            cat_cols = cat_cols[:max_cat_cols]
        
        # Monta descrição do tipo de colunas usadas
        tipo_colunas = []
        if info["nativas"]:
            tipo_colunas.append(f"{len(info['nativas'])} nativas")
        if info["potencialmente_categoricas"]:
            tipo_colunas.append(f"{len(info['potencialmente_categoricas'])} pseudo-categóricas")
        if info["discretizadas"]:
            tipo_colunas.append(f"{len(info['discretizadas'])} discretizadas")
        
        tipo_desc = " + ".join(tipo_colunas) if tipo_colunas else "nenhuma"
        
        print(f"   Colunas categóricas: {len(cat_cols)}")
        print(f"     • Nativas: {len(info['nativas'])}")
        print(f"     • Potencialmente categóricas (≤{MAX_UNIQUE_VALUES_CATEGORICAL} valores): {len(info['potencialmente_categoricas'])}")
        print(f"     • Discretizadas ({N_BINS} bins): {len(info['discretizadas'])}")

        for model_id, model_cfg in MODELS.items():
            print(f"   ▶ {model_cfg['name']}...", end=" ", flush=True)
            try:
                t0 = time.time()
                result_df = model_cfg["detect"](
                    df=df_cat, columns=cat_cols, contamination=true_contamination
                )
                elapsed = time.time() - t0

                y_scores = _score_col(model_id, result_df)
                y_pred   = _anomaly_col(model_id, result_df)

                metrics = avaliar_modelo(y_true, y_pred, y_scores)
                metrics.update({
                    "modelo":               model_id,
                    "dataset":              dataset_name,
                    "tempo_segundos":       elapsed,
                    "contamination_real":   true_contamination,
                    "contamination_predita": float(y_pred.mean()),
                    "n_cat_cols":           len(cat_cols),
                    "tipo_colunas":         tipo_desc,
                })
                all_results.append(metrics)
                print(f"✅  F1={metrics['f1']:.4f} | AUC={metrics.get('auc_roc',0):.4f} | {elapsed:.2f}s")
            except Exception as e:
                print(f"❌  {str(e)[:80]}")

    if not all_results:
        print("\n❌ Nenhum resultado obtido!")
        return None

    results_df = pd.DataFrame(all_results)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(output_dir, f"benchmark_categorico_{ts}.csv")
    results_df.to_csv(csv_path, index=False)
    print(f"\n📁 CSV: {csv_path}")

    pdf_path = os.path.join(output_dir, f"relatorio_categorico_{ts}.pdf")
    gerar_pdf_resultados(results_df, pdf_path)

    return results_df


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
    DATASETS_DIR = os.path.join(SCRIPT_DIR, "datasets", "Classical")
    OUTPUT_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "benchmark_results"))

    # Datasets recomendados (todos têm alguma coluna com potencial categórico)
    DATASETS = [
        (os.path.join(DATASETS_DIR, "45_wine.npz"),            "Wine",            0.0775),
        (os.path.join(DATASETS_DIR, "6_cardio.npz"),           "Cardio",          0.0961),
        (os.path.join(DATASETS_DIR, "38_thyroid.npz"),         "Thyroid",         0.0247),
        (os.path.join(DATASETS_DIR, "27_PageBlocks.npz"),      "PageBlocks",      0.0946),
        (os.path.join(DATASETS_DIR, "7_Cardiotocography.npz"), "Cardiotocography",0.2204),
        (os.path.join(DATASETS_DIR, "29_Pima.npz"),            "Pima",            0.3490),  # diabetes
        (os.path.join(DATASETS_DIR, "2_annthyroid.npz"),       "Annthyroid",      0.0742),  # tem categorias
    ]

    resultados = executar_benchmark(
        DATASETS,
        output_dir=OUTPUT_DIR,
        max_cat_cols=20,
    )

    if resultados is not None:
        print(f"\n✅ Benchmark concluído! {len(resultados)} execuções registradas.")
    else:
        print("\n❌ Benchmark falhou.")