"""
Script de Benchmark para Detecção de Anomalias — Modelos Numéricos
===================================================================

Avalia múltiplos detectores numéricos e gera um PDF com layout aprimorado.

Parâmetros ajustáveis (edite diretamente no início do arquivo):
  - CONTAMINATION: fração esperada de anomalias (padrão: 0.05 = 5%)
  - DATASETS: lista de datasets a serem testados

Uso: python benchmark_numeric_models_test.py
"""

import numpy as np
import pandas as pd
import time
import os
import sys
import argparse
from datetime import datetime
from sklearn.metrics import (
    f1_score, precision_score, recall_score,
    roc_auc_score, average_precision_score,
    confusion_matrix
)
import warnings
warnings.filterwarnings("ignore")

# ============================================================================
# PARÂMETROS AJUSTÁVEIS (edite aqui)
# ============================================================================

# 🔥 CONTAMINATION (threshold) padrão
# Altere este valor para testar diferentes níveis de anomalia
# Exemplos: 0.01 (1%), 0.05 (5%), 0.10 (10%), 0.20 (20%)
DEFAULT_CONTAMINATION = 0.05

# 🔥 Datasets a serem testados
# Cada linha: (caminho, nome_display, taxa_real_opcional)
DATASETS_CONFIG = [
    ("datasets/Classical/6_cardio.npz",          "Cardio",          0.0961),
    ("datasets/Classical/7_Cardiotocography.npz", "Cardiotocography",0.2204),
    ("datasets/Classical/45_wine.npz",            "Wine",            0.0775),
    ("datasets/Classical/38_thyroid.npz",         "Thyroid",         0.0247),
    ("datasets/Classical/27_PageBlocks.npz",      "PageBlocks",      0.0946),
]

# ============================================================================
# IMPORTAÇÃO DOS DETECTORES
# ============================================================================

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.numeric.zscore_service      import detect as zscore_detect
from services.numeric.iforest_service     import detect as iforest_detect
from services.numeric.iqr_service         import detect as iqr_detect
from services.numeric.knn_service         import detect as knn_detect
from services.numeric.lof_service         import detect as lof_detect
from services.numeric.mad_service         import detect as mad_detect
from services.numeric.mahalanobis_service import detect as mahalanobis_detect
from services.numeric.percentile_service  import detect as percentile_detect


# ============================================================================
# PALETA E CONFIGURAÇÃO VISUAL
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

MODELS = {
    "zscore":       {"detect": zscore_detect,       "name": "Z-Score"},
    "iforest":      {"detect": iforest_detect,      "name": "Isolation Forest"},
    "iqr":          {"detect": iqr_detect,           "name": "IQR (Tukey)"},
    "knn":          {"detect": knn_detect,           "name": "KNN Distance"},
    "lof":          {"detect": lof_detect,           "name": "LOF"},
    "mad":          {"detect": mad_detect,           "name": "MAD (Z-Score Modificado)"},
    "mahalanobis":  {"detect": mahalanobis_detect,  "name": "Mahalanobis"},
    "percentile":   {"detect": percentile_detect,   "name": "Percentile Fence"},
}

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def carregar_dataset(caminho: str):
    data = np.load(caminho, allow_pickle=True)
    X, y = data["X"], data["y"]
    colunas = [f"feature_{i}" for i in range(X.shape[1])]
    df = pd.DataFrame(X, columns=colunas)
    return df, y.astype(int)


def avaliar_modelo(y_true, y_pred, y_scores=None):
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


# ============================================================================
# GERAÇÃO DO PDF
# ============================================================================

def _hex(color: str):
    from reportlab.lib import colors as rl_colors
    return rl_colors.HexColor(color)


def _score_color(value: float, metric: str = "f1"):
    if np.isnan(value):
        return _hex(TEXT_MUTED)
    if metric in ("f1", "auc_roc", "precision", "recall"):
        if value >= 0.7:
            return _hex(GREEN_SOFT)
        if value >= 0.4:
            return _hex(YELLOW_SOFT)
        return _hex(RED_SOFT)
    return _hex(TEXT_DARK)


def gerar_pdf_resultados(results_df: pd.DataFrame, output_path: str, tipo: str = "Numérico", contamination: float = 0.05):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors as rl_colors
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
    S_SUBTITLE = PS("ST", fontSize=11, textColor=_hex(ACCENT_GREEN), alignment=TA_CENTER,
                    fontName="Helvetica", leading=16)
    S_CAPTION  = PS("CAP", fontSize=8, textColor=_hex(TEXT_MUTED), alignment=TA_CENTER)
    S_SECTION  = PS("SEC", fontSize=13, textColor=_hex(DARK_BG), fontName="Helvetica-Bold",
                    spaceBefore=14, spaceAfter=6)
    S_LABEL    = PS("LBL", fontSize=7, textColor=_hex(TEXT_MUTED))

    def hr(color=MID_GRAY, thickness=0.5):
        return HRFlowable(width="100%", thickness=thickness, color=_hex(color), spaceAfter=6, spaceBefore=6)

    story = []

    # CAPA
    capa_header = Table(
        [[Paragraph(f"Benchmark de Detecção de Anomalias — Modelos {tipo}", S_TITLE)],
         [Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}  ·  "
                    f"Contamination: {contamination:.0%}  ·  "
                    f"{len(results_df['modelo'].unique())} modelos  ·  "
                    f"{len(results_df['dataset'].unique())} datasets", S_SUBTITLE)]],
        colWidths=[W - 3*cm],
    )
    capa_header.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), _hex(DARK_BG)),
        ("TOPPADDING",   (0,0), (-1,-1), 18),
        ("BOTTOMPADDING",(0,0), (-1,-1), 18),
        ("LEFTPADDING",  (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
    ]))
    story.append(capa_header)
    story.append(Spacer(1, 0.6*cm))

    # KPIs
    ranking = results_df.groupby("modelo")["f1"].mean().sort_values(ascending=False)
    best_model = MODELS.get(ranking.index[0], {}).get("name", ranking.index[0])
    best_f1    = ranking.iloc[0]
    avg_auc    = results_df["auc_roc"].mean()
    avg_time   = results_df["tempo_segundos"].mean()
    n_datasets = len(results_df["dataset"].unique())

    def kpi_card(title, value, sub=""):
        inner = Table([[Paragraph(title, S_LABEL)],
                       [Paragraph(value, PS("KV", fontSize=16, fontName="Helvetica-Bold",
                                            textColor=_hex(ACCENT_GREEN), alignment=TA_CENTER))],
                       [Paragraph(sub, S_CAPTION)]], colWidths=[4.8*cm])
        inner.setStyle(TableStyle([
            ("ALIGN", (0,0), (-1,-1), "CENTER"), ("BACKGROUND", (0,0), (-1,-1), _hex(LIGHT_GRAY)),
            ("TOPPADDING", (0,0), (-1,-1), 10), ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("LINEBELOW", (0,0), (-1,0), 2, _hex(ACCENT_GREEN)),
        ]))
        return inner

    kpis = Table([[
        kpi_card("Melhor Modelo", best_model, f"F1 médio: {best_f1:.4f}"),
        kpi_card("AUC-ROC Médio", f"{avg_auc:.4f}", "Todos modelos/datasets"),
        kpi_card("Tempo Médio", f"{avg_time:.2f}s", "Por execução"),
        kpi_card("Datasets", str(n_datasets), "Avaliados"),
    ]], colWidths=[4.8*cm]*4, hAlign="CENTER")
    story.append(kpis)
    story.append(Spacer(1, 0.5*cm))
    story.append(hr(ACCENT_GREEN, thickness=1.5))

    # =========================================================================
    # RANKING
    # =========================================================================
    story.append(Paragraph("1. Ranking Geral dos Modelos (F1-Score Médio)", S_SECTION))

    rank_df = results_df.groupby("modelo").agg(
        f1=("f1","mean"), precision=("precision","mean"),
        recall=("recall","mean"), auc_roc=("auc_roc","mean"),
        tempo=("tempo_segundos","mean"),
    ).round(4).sort_values("f1", ascending=False).reset_index()

    max_f1 = rank_df["f1"].max() if rank_df["f1"].max() > 0 else 1

    def bar_cell(value, max_val, width_pts=110):
        d = Drawing(width_pts, 14)
        bar_w = max(2, int((value / max_val) * (width_pts - 4)))
        d.add(Rect(0, 3, width_pts - 4, 8, fillColor=_hex(MID_GRAY), strokeColor=None))
        d.add(Rect(0, 3, bar_w, 8, fillColor=_hex(ACCENT_GREEN), strokeColor=None))
        d.add(String(width_pts - 2, 4, f"{value:.4f}", fontSize=7, fillColor=_hex(TEXT_DARK), textAnchor="end"))
        return d

    rank_header = [["#", "Modelo", "F1-Score", "Precision", "Recall", "AUC-ROC", "Tempo (s)"]]
    rank_rows = []
    for i, row in rank_df.iterrows():
        rank_rows.append([
            str(i+1), MODELS.get(row["modelo"], {}).get("name", row["modelo"]),
            bar_cell(row["f1"], max_f1), f"{row['precision']:.4f}", f"{row['recall']:.4f}",
            f"{row['auc_roc']:.4f}" if not np.isnan(row["auc_roc"]) else "—",
            f"{row['tempo']:.2f}s",
        ])

    rank_table = Table(rank_header + rank_rows, colWidths=None, repeatRows=1)
    rank_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), _hex(DARK_BG)), ("TEXTCOLOR", (0,0), (-1,0), _hex(WHITE)),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ALIGN", (0,0), (-1,-1), "CENTER"), ("GRID", (0,0), (-1,-1), 0.3, _hex(MID_GRAY)),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [_hex(WHITE), _hex(LIGHT_GRAY)]),
        ("BACKGROUND", (0,1), (-1,1), _hex("#E8FDF7")),
    ]))
    story.append(rank_table)
    story.append(Spacer(1, 0.4*cm))

    # Resultados detalhados por modelo (omitido para brevidade, mantenha o original)
    # ... (o resto do código de geração do PDF permanece igual)

    doc.build(story)
    print(f"✅ PDF gerado: {output_path}")


# ============================================================================
# EXECUÇÃO DO BENCHMARK
# ============================================================================

def executar_benchmark(datasets: list, output_dir: str = "benchmark_results", contamination: float = DEFAULT_CONTAMINATION):
    """
    Executa benchmark com threshold ajustável.
    
    Parâmetros
    ----------
    datasets     : lista de (caminho, nome, contaminação_real)
    output_dir   : diretório para CSV e PDF
    contamination : fração esperada de anomalias (threshold)
    """
    os.makedirs(output_dir, exist_ok=True)
    all_results = []

    print("=" * 70)
    print("BENCHMARK — MODELOS NUMÉRICOS")
    print(f"Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Contamination (threshold): {contamination:.0%}")
    print(f"Modelos: {len(MODELS)}  |  Datasets: {len(datasets)}")
    print("=" * 70)

    for dataset_path, dataset_name, true_contamination in datasets:
        print(f"\n📊 {dataset_name}  (contaminação real: {true_contamination:.2%})")

        try:
            df, y_true = carregar_dataset(dataset_path)
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) < 2:
                print(f"   ⚠️ Apenas {len(numeric_cols)} coluna(s) numérica(s). Pulando...")
                continue
            print(f"   Shape: {df.shape}  |  Anomalias reais: {y_true.sum()} ({y_true.mean():.2%})")
        except Exception as e:
            print(f"   ❌ Erro ao carregar: {e}")
            continue

        for model_id, model_cfg in MODELS.items():
            print(f"   ▶ {model_cfg['name']}...", end=" ", flush=True)
            try:
                t0 = time.time()
                result_df = model_cfg["detect"](
                    df=df, columns=numeric_cols, contamination=contamination  # ← USANDO contamination
                )
                elapsed = time.time() - t0

                y_scores = result_df.get(f"{model_id}_score", pd.Series(dtype=float)).values
                y_pred   = result_df[f"{model_id}_anomaly"].values

                metrics = avaliar_modelo(y_true, y_pred, y_scores)
                metrics.update({
                    "modelo":               model_id,
                    "dataset":              dataset_name,
                    "tempo_segundos":       elapsed,
                    "contamination_real":   true_contamination,
                    "contamination_predita": float(y_pred.mean()),
                })
                all_results.append(metrics)
                print(f"✅ F1={metrics['f1']:.4f} | AUC={metrics.get('auc_roc', 0):.4f} | {elapsed:.2f}s")
            except Exception as e:
                print(f"❌ {str(e)[:80]}")

    if not all_results:
        print("\n❌ Nenhum resultado obtido!")
        return None

    results_df = pd.DataFrame(all_results)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(output_dir, f"benchmark_numerico_{ts}.csv")
    results_df.to_csv(csv_path, index=False)
    print(f"\n📁 CSV: {csv_path}")

    pdf_path = os.path.join(output_dir, f"relatorio_numerico_{ts}.pdf")
    gerar_pdf_resultados(results_df, pdf_path, tipo="Numérico", contamination=contamination)

    return results_df


# ============================================================================
# MAIN
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark de modelos numéricos")
    parser.add_argument("--contamination", "-c", type=float, default=DEFAULT_CONTAMINATION,
                        help=f"Threshold (contamination). Padrão: {DEFAULT_CONTAMINATION:.0%}")
    parser.add_argument("--output", "-o", type=str, default="benchmark_results",
                        help="Diretório de saída")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
    DATASETS_DIR = os.path.join(SCRIPT_DIR, "datasets", "Classical")
    OUTPUT_DIR   = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", args.output))

    # Atualiza os caminhos dos datasets
    DATASETS = []
    for path, name, cont in DATASETS_CONFIG:
        full_path = os.path.join(DATASETS_DIR, os.path.basename(path))
        DATASETS.append((full_path, name, cont))

    print(f"\n🎯 Threshold utilizado: {args.contamination:.0%}")
    
    resultados = executar_benchmark(DATASETS, output_dir=OUTPUT_DIR, contamination=args.contamination)

    if resultados is not None:
        print(f"\n✅ Benchmark concluído! {len(resultados)} execuções registradas.")
    else:
        print("\n❌ Benchmark falhou.")