from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..services.registry import get_models_list, run_selected
from ..models.report import ReportRequest, ReportResponse
from ..models.database import supabase

import os, io, csv
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/report", tags=["report"])

# Armazena o último relatório em memória
_last_report: dict | None = None
_last_df_result: pd.DataFrame | None = None


@router.get("/models")
def list_models():
    """Retorna todos os detectores disponíveis separados por tipo."""
    return get_models_list()


@router.post("/generate/{file_id}", response_model=ReportResponse)
def generate_report(info: ReportRequest, file_id: str):
    global _last_report, _last_df_result

    # 1. Verifica se o arquivo existe no banco
    try:
        file_record = (
            supabase.table(os.getenv("SUPABASE_TABLE"))
            .select("*")
            .eq("id", file_id)
            .maybe_single()
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao consultar banco: {str(e)}")

    if not file_record.data:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    record = file_record.data
    filename = record["filename"]
    size_bytes = record.get("size_bytes", 0)

    # 2. Baixa o CSV do Supabase Storage
    try:
        raw = supabase.storage.from_(os.getenv("SUPABASE_BUCKET")).download(
            record["storage_path"]
        )
        
        if len(raw) == 0:
            raise ValueError("Arquivo está vazio")
        
        # Decodifica primeiras linhas para análise
        try:
            preview = raw.decode('utf-8', errors='ignore')[:2048]
        except:
            preview = raw.decode('latin1', errors='ignore')[:2048]
        
        # Detecta se o Supabase retornou erro HTML
        if '<html' in preview.lower() or '<!doctype' in preview.lower():
            error_msg = f"Supabase retornou HTML de erro: {preview[:200]}"
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Detecta delimitador
        first_line = preview.split('\n')[0]
        if first_line.count(';') > first_line.count(','):
            delimiter = ';'
        elif first_line.count('\t') > first_line.count(','):
            delimiter = '\t'
        elif first_line.count('|') > first_line.count(','):
            delimiter = '|'
        else:
            delimiter = ','
        
        # Tenta múltiplas estratégias de leitura
        try:
            df = pd.read_csv(
                io.BytesIO(raw),
                sep=delimiter,
                engine='python',
                on_bad_lines='skip',
                quotechar='"',
                encoding='utf-8'
            )
        except:
            df = pd.read_csv(
                io.BytesIO(raw),
                sep=delimiter,
                engine='c',
                on_bad_lines='skip',
                encoding='utf-8'
            )
        
        if len(df.columns) == 0:
            raise ValueError(f"Não foi possível identificar colunas. Preview: {preview[:200]}")
        
        print(f"✅ CSV lido: {len(df)} linhas, {len(df.columns)} colunas")
        
    except Exception as e:
        error_detail = f"Falha ao ler arquivo: {str(e)}"
        if 'raw' in locals():
            error_detail += f" | Tamanho: {len(raw)} bytes"
        raise HTTPException(status_code=500, detail=error_detail)

    num_cols = info.colunas_numericas
    cat_cols = info.colunas_categoricas

    # 3. Roda os detectores selecionados
    try:
        df_result = run_selected(
            df=df,
            model_ids=info.selecionados,
            numeric_cols=num_cols,
            categorical_cols=cat_cols,
            contamination=0.05,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha na detecção: {e}")

    # 4. Monta análise geral por coluna
    analise_geral = {}

    for col in num_cols:
        if col not in df.columns:
            continue
        serie = df[col].dropna()
        if len(serie) == 0:
            continue
        q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
        iqr = q3 - q1
        outliers_iqr = int(((serie < q1 - 1.5 * iqr) | (serie > q3 + 1.5 * iqr)).sum())

        try:
            bins = pd.cut(serie, bins=5)
            intervalos = {str(k): int(v) for k, v in bins.value_counts().sort_index().items()}
        except:
            intervalos = {}

        analise_geral[col] = {
            "tipo": "numerico",
            "nulls": int(df[col].isna().sum()),
            "outliers": outliers_iqr,
            "intervalos": intervalos,
        }

    for col in cat_cols:
        if col not in df.columns:
            continue
        freq = df[col].value_counts(normalize=True).head(10)
        analise_geral[col] = {
            "tipo": "categorico",
            "nulls": int(df[col].isna().sum()),
            "outliers": 0,
            "frequencia": {str(k): round(float(v), 4) for k, v in freq.items()},
        }

    # 5. Estatísticas descritivas (só numéricas)
    estatisticas = {}
    for col in num_cols:
        if col not in df.columns:
            continue
        serie = df[col].dropna()
        if len(serie) == 0:
            continue
        estatisticas[col] = {
            "min":    round(float(serie.min()), 4),
            "max":    round(float(serie.max()), 4),
            "media":  round(float(serie.mean()), 4),
            "mediana": round(float(serie.median()), 4),
            "q1":     round(float(serie.quantile(0.25)), 4),
            "q3":     round(float(serie.quantile(0.75)), 4),
        }

    # 6. Resultados por modelo
    modelos_resultado = {}
    score_cols = [c for c in df_result.columns if c.endswith("_score")]

    prefixes = sorted({c.rsplit("_", 1)[0] for c in score_cols})
    for prefix in prefixes:
        sc = f"{prefix}_score"
        an = f"{prefix}_anomaly"
        if sc not in df_result.columns:
            continue
        rows = []
        for i, row in df_result.iterrows():
            entry = {"linha": int(i)}
            for col in num_cols + cat_cols:
                if col in df_result.columns:
                    val = row[col]
                    entry[col] = None if pd.isna(val) else (
                        round(float(val), 4) if isinstance(val, (float, np.floating)) else val
                    )
            entry["score"] = round(float(row[sc]), 6) if not pd.isna(row[sc]) else None
            entry["anomalia"] = int(row[an]) if an in df_result.columns else 0
            rows.append(entry)
        modelos_resultado[prefix] = rows

    # 7. Monta o relatório completo
    report = {
        "arquivo": {
            "nome": filename,
            "tipo": record.get("content_type", "text/csv"),
            "linhas": int(len(df)),
            "colunas": int(len(df.columns)),
            "tamanho": f"{round(size_bytes / 1024, 1)} KB",
        },
        "analise_geral": analise_geral,
        "estatisticas": estatisticas,
        "modelos": modelos_resultado,
        "colunas_selecionadas": {
            "numericas": num_cols,
            "categoricas": cat_cols,
            "modelos_aplicados": info.selecionados
        }
    }

    _last_report = report
    _last_df_result = df_result

    return report


@router.get("")
def get_report():
    if _last_report is None:
        raise HTTPException(status_code=404, detail="Nenhum relatório gerado ainda.")
    return _last_report


@router.get("/cleaned")
def download_cleaned():
    if _last_df_result is None:
        raise HTTPException(status_code=404, detail="Nenhum relatório gerado ainda.")

    buf = io.StringIO()
    _last_df_result.to_csv(buf, index=False)
    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dados_tratados.csv"},
    )


@router.get("/pdf")
def download_pdf():
    """Gera um PDF simplificado e direto com informações essenciais do relatório."""
    if _last_report is None:
        raise HTTPException(status_code=404, detail="Nenhum relatório gerado ainda.")

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
            HRFlowable, PageBreak
        )
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="reportlab não instalado. Execute: pip install reportlab"
        )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    GREEN  = colors.HexColor("#05CB9D")
    NAVY   = colors.HexColor("#0D1B2A")
    LIGHT  = colors.HexColor("#F5F5F5")
    WHITE  = colors.white
    RED_BG = colors.HexColor("#FDE8E8")
    ORANGE = colors.HexColor("#F39C12")

    styles = getSampleStyleSheet()
    
    h1 = ParagraphStyle("h1", fontSize=18, textColor=NAVY, spaceAfter=8,
                         fontName="Helvetica-Bold", alignment=TA_CENTER)
    h2 = ParagraphStyle("h2", fontSize=13, textColor=NAVY, spaceBefore=16,
                         spaceAfter=8, fontName="Helvetica-Bold")
    h3 = ParagraphStyle("h3", fontSize=11, textColor=NAVY, spaceBefore=12,
                         spaceAfter=6, fontName="Helvetica-Bold")
    normal = ParagraphStyle("normal", fontSize=9, textColor=NAVY,
                             fontName="Helvetica", spaceAfter=4)
    bullet = ParagraphStyle("bullet", fontSize=9, textColor=NAVY,
                             fontName="Helvetica", leftIndent=10, bulletIndent=10, spaceAfter=2)
    
    def tbl_style_header():
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
    
    def tbl_style_simple():
        return TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ])

    story = []
    r = _last_report

    # ──────────────────────────────────────────────────────────────────────
    # TÍTULO PRINCIPAL
    # ──────────────────────────────────────────────────────────────────────
    story.append(Paragraph(f"Relatório de Detecção de Anomalias", h1))
    story.append(Paragraph(f"{r['arquivo']['nome']}", h2))
    story.append(HRFlowable(width="100%", thickness=2, color=GREEN, spaceAfter=12))

    # ──────────────────────────────────────────────────────────────────────
    # 1. INFORMAÇÕES BÁSICAS DO ARQUIVO
    # ──────────────────────────────────────────────────────────────────────
    story.append(Paragraph("📁 1. Informações Básicas do Arquivo", h2))
    
    info_data = [
        ["Nome do arquivo", r["arquivo"]["nome"]],
        ["Tipo", r["arquivo"]["tipo"]],
        ["Total de linhas", f"{r['arquivo']['linhas']:,}"],
        ["Total de colunas", str(r["arquivo"]["colunas"])],
        ["Tamanho", r["arquivo"]["tamanho"]],
    ]
    
    t = Table(info_data, colWidths=[4.5*cm, 10*cm])
    t.setStyle(tbl_style_simple())
    story.append(t)
    story.append(Spacer(1, 0.3*cm))

    # ──────────────────────────────────────────────────────────────────────
    # 2. COLUNAS SELECIONADAS PARA ANÁLISE (formato de lista por linha)
    # ──────────────────────────────────────────────────────────────────────
    story.append(Paragraph("📊 2. Colunas Selecionadas para Análise", h2))
    
    colunas_selecionadas = r.get("colunas_selecionadas", {})
    numericas = colunas_selecionadas.get("numericas", [])
    categoricas = colunas_selecionadas.get("categoricas", [])
    modelos_aplicados = colunas_selecionadas.get("modelos_aplicados", [])
    
    # Formata as listas como texto com quebra de linha
    numericas_text = "\n".join([f"• {col}" for col in numericas]) if numericas else "Nenhuma coluna numérica selecionada"
    categoricas_text = "\n".join([f"• {col}" for col in categoricas]) if categoricas else "Nenhuma coluna categórica selecionada"
    modelos_text = "\n".join([f"• {modelo}" for modelo in modelos_aplicados]) if modelos_aplicados else "Nenhum modelo aplicado"
    
    colunas_data = [
        ["Tipo", "Quantidade", "Colunas"],
        ["Numéricas", str(len(numericas)), Paragraph(numericas_text.replace("\n", "<br/>"), normal)],
        ["Categóricas", str(len(categoricas)), Paragraph(categoricas_text.replace("\n", "<br/>"), normal)],
        ["Modelos Aplicados", str(len(modelos_aplicados)), Paragraph(modelos_text.replace("\n", "<br/>"), normal)],
    ]
    
    t = Table(colunas_data, colWidths=[3*cm, 2.5*cm, 10*cm])
    t.setStyle(tbl_style_header())
    story.append(t)
    story.append(Spacer(1, 0.3*cm))

    # ──────────────────────────────────────────────────────────────────────
    # 3. RESUMO DAS COLUNAS (Análise Geral)
    # ──────────────────────────────────────────────────────────────────────
    story.append(Paragraph("🔍 3. Resumo das Colunas", h2))
    
    resumo_data = [["Coluna", "Tipo", "Nulos (%)", "Outliers", "Destaque"]]
    
    for col, info in list(r["analise_geral"].items())[:15]:
        nulos_pct = (info["nulls"] / r["arquivo"]["linhas"]) * 100 if r["arquivo"]["linhas"] > 0 else 0
        destaque = ""
        if info["outliers"] > 0:
            destaque = f"⚠️ {info['outliers']} outliers"
        if nulos_pct > 30:
            destaque = "⚠️ Alta taxa de nulos"
        
        resumo_data.append([
            col,
            "Numérico" if info["tipo"] == "numerico" else "Categórico",
            f"{info['nulls']} ({nulos_pct:.1f}%)",
            str(info["outliers"]),
            destaque if destaque else "✓ OK"
        ])
    
    t = Table(resumo_data, colWidths=[4*cm, 2.5*cm, 2.5*cm, 2*cm, 4*cm])
    t.setStyle(tbl_style_header())
    story.append(t)
    
    if len(r["analise_geral"]) > 15:
        story.append(Paragraph(f"* Exibindo 15 de {len(r['analise_geral'])} colunas", normal))
    
    story.append(Spacer(1, 0.3*cm))

    # ──────────────────────────────────────────────────────────────────────
    # 4. RESULTADOS POR MODELO (sem tabela de score, apenas estatísticas)
    # ──────────────────────────────────────────────────────────────────────
    story.append(Paragraph("🤖 4. Resultados por Modelo", h2))
    
    for modelo_nome, rows in r["modelos"].items():
        if not rows:
            continue
        
        anomalias = sum(1 for row in rows if row.get("anomalia") == 1)
        total = len(rows)
        taxa = (anomalias / total) * 100 if total > 0 else 0
        
        # Cabeçalho do modelo
        story.append(Paragraph(f"Modelo: {modelo_nome}", h3))
        
        # Estatísticas do modelo
        stats_data = [
            ["Total de registros", str(total)],
            ["Anomalias detectadas", f"{anomalias} ({taxa:.1f}%)"],
            ["Registros normais", str(total - anomalias)],
        ]
        
        # Adiciona score médio se disponível
        scores = [row.get("score", 0) for row in rows if row.get("score") is not None]
        if scores:
            score_medio = sum(scores) / len(scores)
            stats_data.append(["Score médio", f"{score_medio:.6f}"])
        
        t = Table(stats_data, colWidths=[5*cm, 10*cm])
        t.setStyle(tbl_style_simple())
        story.append(t)
        
        # Adiciona um mini gráfico de barras visual (textual) para representar a taxa
        bar_length = int(taxa / 2)  # escala: 100% = 50 caracteres
        bar_normal = 50 - bar_length
        bar_chart = f"[{'█' * bar_length}{'░' * bar_normal}] {taxa:.1f}%"
        
        story.append(Paragraph(f"Taxa de anomalia: {bar_chart}", normal))
        story.append(Spacer(1, 0.2*cm))
    
    # ──────────────────────────────────────────────────────────────────────
    # 5. RESUMO FINAL
    # ──────────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN, spaceAfter=8))
    story.append(Paragraph("📌 5. Resumo Final", h2))
    
    total_anomalias_geral = sum(
        sum(1 for row in rows if row.get("anomalia") == 1) 
        for rows in r["modelos"].values()
    )
    total_registros_geral = sum(len(rows) for rows in r["modelos"].values())
    taxa_media = (total_anomalias_geral / total_registros_geral) * 100 if total_registros_geral > 0 else 0
    
    resumo_final_data = [
        ["Total de modelos executados", str(len(r["modelos"]))],
        ["Total de anomalias detectadas", str(total_anomalias_geral)],
        ["Taxa média de anomalia", f"{taxa_media:.2f}%"],
    ]
    
    t = Table(resumo_final_data, colWidths=[6*cm, 9*cm])
    t.setStyle(tbl_style_simple())
    story.append(t)
    
    # Barra visual da taxa média
    bar_length = int(taxa_media / 2)
    bar_normal = 50 - bar_length
    bar_chart = f"[{'█' * bar_length}{'░' * bar_normal}] {taxa_media:.1f}%"
    story.append(Paragraph(f"Taxa média de anomalia: {bar_chart}", normal))
    
    if total_anomalias_geral == 0:
        story.append(Paragraph("✅ Nenhuma anomalia foi detectada nos modelos aplicados.", normal))
    elif taxa_media > 10:
        story.append(Paragraph("⚠️ Atenção: Taxa de anomalia superior a 10%. Recomenda-se revisar os dados.", normal))
    else:
        story.append(Paragraph("✓ Detecção concluída com taxas normais de anomalia.", normal))
    
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Relatório gerado em {pd.Timestamp.now().strftime('%d/%m/%Y às %H:%M')}", 
                          ParagraphStyle("footer", fontSize=8, textColor=colors.HexColor("#999999"), alignment=TA_CENTER)))

    doc.build(story)
    buf.seek(0)

    return StreamingResponse(
        iter([buf.read()]),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relatorio.pdf"},
    )