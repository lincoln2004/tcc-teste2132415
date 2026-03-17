from collections import Counter
from typing import Any

import numpy as np
import pandas as pd


class DetalhadorAnalise:
    """
    Construtor de resumos descritivos, taxonomias e explicacoes linha a linha das anomalias.
    """

    CATALOGO_TIPOS_ANOMALIA = {
        "zscore_acima_limite_superior": {
            "nome": "Desvio extremo acima da media",
            "descricao": "O registro ficou muito acima do comportamento medio esperado na coluna principal.",
            "criterio": "Z-Score maior que o limiar configurado e valor acima da media.",
            "algoritmo": "zscore",
        },
        "zscore_abaixo_limite_inferior": {
            "nome": "Desvio extremo abaixo da media",
            "descricao": "O registro ficou muito abaixo do comportamento medio esperado na coluna principal.",
            "criterio": "Z-Score maior que o limiar configurado e valor abaixo da media.",
            "algoritmo": "zscore",
        },
        "zscore_multicoluna": {
            "nome": "Desvio simultaneo em varias colunas",
            "descricao": "Mais de uma coluna ultrapassou o limiar de desvio padrao no mesmo registro.",
            "criterio": "Duas ou mais colunas com Z-Score acima do threshold na mesma linha.",
            "algoritmo": "zscore",
        },
        "iqr_acima_limite_superior": {
            "nome": "Valor acima do limite interquartil",
            "descricao": "O registro ficou acima do limite superior calculado a partir dos quartis.",
            "criterio": "Valor acima de Q3 + fator * IQR.",
            "algoritmo": "iqr",
        },
        "iqr_abaixo_limite_inferior": {
            "nome": "Valor abaixo do limite interquartil",
            "descricao": "O registro ficou abaixo do limite inferior calculado a partir dos quartis.",
            "criterio": "Valor abaixo de Q1 - fator * IQR.",
            "algoritmo": "iqr",
        },
        "iqr_multicoluna": {
            "nome": "Ruptura interquartil em varias colunas",
            "descricao": "Mais de uma coluna ficou fora dos limites interquartis no mesmo registro.",
            "criterio": "Duas ou mais colunas fora dos limites interquartis na mesma linha.",
            "algoritmo": "iqr",
        },
        "isolation_forest_desvio_dominante": {
            "nome": "Desvio dominante em uma coluna",
            "descricao": "O modelo isolou o registro principalmente por causa de um valor muito distante em uma coluna.",
            "criterio": "Uma coluna concentrou a maior parte do desvio que levou ao isolamento do registro.",
            "algoritmo": "isolation_forest",
        },
        "isolation_forest_combinacao_rara": {
            "nome": "Combinacao rara de variaveis",
            "descricao": "O modelo entendeu que a combinacao de varias colunas tornou o registro raro.",
            "criterio": "O isolamento ocorreu pelo conjunto de variaveis e nao apenas por uma coluna dominante.",
            "algoritmo": "isolation_forest",
        },
        "lof_desvio_dominante": {
            "nome": "Desvio local dominante",
            "descricao": "A baixa densidade local foi puxada principalmente por uma coluna muito distante.",
            "criterio": "Uma coluna respondeu pela maior parte da diferenca local frente aos vizinhos.",
            "algoritmo": "lof",
        },
        "lof_combinacao_atipica": {
            "nome": "Contexto local atipico",
            "descricao": "A combinacao de valores deixou o registro pouco semelhante ao grupo de vizinhos mais proximos.",
            "criterio": "O LOF detectou densidade local anormal a partir de mais de uma coluna relevante.",
            "algoritmo": "lof",
        },
    }

    @staticmethod
    def normalizar_numero(valor: Any, casas: int = 6) -> float | None:
        """
        Converte um valor numerico para float arredondado e compativel com JSON.
        """
        if valor is None or pd.isna(valor):
            return None
        return round(float(valor), casas)

    @staticmethod
    def serializar_valor(valor: Any) -> Any:
        """
        Converte valores do DataFrame para formatos simples de serializacao.
        """
        if valor is None or pd.isna(valor):
            return None
        if isinstance(valor, (np.integer, np.floating)):
            return valor.item()
        return valor

    @staticmethod
    def montar_dados_registro(df_original: pd.DataFrame, indice_posicional: int, colunas: list[str]) -> dict[str, Any]:
        """
        Extrai os valores originais das colunas analisadas para um registro especifico.
        """
        linha = df_original.iloc[indice_posicional]
        return {
            coluna: DetalhadorAnalise.serializar_valor(linha[coluna])
            for coluna in colunas
            if coluna in linha.index
        }

    @staticmethod
    def obter_localizacao_registro(indice_posicional: int, indice_original: Any) -> str:
        """
        Gera uma descricao amigavel da localizacao do registro dentro do dataset.
        """
        return (
            f"Registro {indice_posicional + 1} do dataset analisado "
            f"(indice original: {DetalhadorAnalise.serializar_valor(indice_original)})."
        )

    @staticmethod
    def compor_resumo_colunas_relevantes(colunas_relevantes: list[dict[str, Any]]) -> str:
        """
        Resume as colunas mais relevantes em uma frase curta para a justificativa.
        """
        descricoes = []
        for coluna in colunas_relevantes:
            score = coluna.get("score_coluna")
            direcao = coluna.get("direcao")
            coluna_nome = coluna["coluna"]

            if score is None:
                descricoes.append(coluna_nome)
                continue

            if direcao:
                descricoes.append(f"{coluna_nome} ({score:.2f}, {direcao})")
            else:
                descricoes.append(f"{coluna_nome} ({score:.2f})")

        if not descricoes:
            return "sem colunas relevantes identificadas"
        if len(descricoes) == 1:
            return descricoes[0]
        return ", ".join(descricoes[:-1]) + f" e {descricoes[-1]}"

    @staticmethod
    def construir_distribuicao_tipos(
        detalhes_anomalias: list[dict[str, Any]],
        total_anomalias: int,
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        """
        Gera a distribuicao por tipo e filtra o dicionario apenas para os tipos encontrados.
        """
        contagem_tipos = Counter(detalhe["tipo_principal"] for detalhe in detalhes_anomalias)
        tipos_encontrados = []
        dicionario_encontrado: dict[str, dict[str, Any]] = {}

        for codigo, quantidade in contagem_tipos.most_common():
            descricao_tipo = DetalhadorAnalise.CATALOGO_TIPOS_ANOMALIA[codigo]
            dicionario_encontrado[codigo] = descricao_tipo
            tipos_encontrados.append(
                {
                    "codigo": codigo,
                    "nome": descricao_tipo["nome"],
                    "quantidade": int(quantidade),
                    "percentual": round((quantidade / total_anomalias) * 100, 2) if total_anomalias else 0.0,
                    "descricao": descricao_tipo["descricao"],
                    "criterio": descricao_tipo["criterio"],
                }
            )

        return tipos_encontrados, dicionario_encontrado

    @staticmethod
    def gerar_interpretacao_geral(
        algoritmo: str,
        total_anomalias: int,
        percentual_anomalias: float,
        score_maximo: float,
        parametros_utilizados: dict[str, Any],
    ) -> str:
        """
        Gera uma interpretacao geral do comportamento do algoritmo para o usuario final.
        """
        if algoritmo == "zscore":
            threshold = float(parametros_utilizados.get("threshold", 3.0))
            if total_anomalias == 0:
                return (
                    f"Nenhum registro ultrapassou o limiar de {threshold:.2f} desvios padrao. "
                    f"O maior Z-Score observado foi {score_maximo:.2f}."
                )
            return (
                f"{total_anomalias} registro(s) ultrapassaram o limiar de {threshold:.2f} desvios padrao, "
                f"representando {percentual_anomalias:.2f}% do dataset."
            )

        if algoritmo == "iqr":
            fator = float(parametros_utilizados.get("fator", 1.5))
            if total_anomalias == 0:
                return (
                    f"Nenhum registro ficou fora dos limites calculados por Q1 - {fator:.2f}*IQR "
                    f"e Q3 + {fator:.2f}*IQR."
                )
            return (
                f"{total_anomalias} registro(s) ficaram fora dos limites interquartis com fator {fator:.2f}, "
                f"equivalendo a {percentual_anomalias:.2f}% do dataset."
            )

        if algoritmo == "isolation_forest":
            contaminacao = float(parametros_utilizados.get("contaminacao", 0.05)) * 100
            return (
                f"O Isolation Forest isolou {total_anomalias} registro(s) como suspeitos. "
                f"A configuracao considera contaminacao estimada de {contaminacao:.2f}%."
            )

        if algoritmo == "lof":
            n_vizinhos = int(parametros_utilizados.get("n_vizinhos", 20))
            return (
                f"O LOF marcou {total_anomalias} registro(s) por apresentarem densidade local atipica "
                f"em comparacao com {n_vizinhos} vizinhos."
            )

        return f"{total_anomalias} registro(s) foram sinalizados para revisao manual."

    @staticmethod
    def construir_detalhes_zscore(
        df_original: pd.DataFrame,
        df_limpo: pd.DataFrame,
        flags_array: np.ndarray,
        scores_array: np.ndarray,
        parametros_utilizados: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Gera explicacoes detalhadas para anomalias detectadas via Z-Score.
        """
        threshold = float(parametros_utilizados.get("threshold", 3.0))
        medias = df_limpo.mean()
        desvios = df_limpo.std(ddof=0).replace(0, np.nan)
        z_scores = ((df_limpo - medias).divide(desvios)).abs().replace([np.inf, -np.inf], np.nan).fillna(0.0)

        detalhes = []

        for indice_posicional, flag in enumerate(flags_array):
            if int(flag) != 1:
                continue

            linha_original = df_original.iloc[indice_posicional]
            linha_limpa = df_limpo.iloc[indice_posicional]
            linha_z = z_scores.iloc[indice_posicional]
            colunas_relevantes = []

            for coluna in df_limpo.columns:
                score_coluna = float(linha_z[coluna])
                if score_coluna <= threshold:
                    continue

                valor_analisado = float(linha_limpa[coluna])
                media = float(medias[coluna])
                desvio = float(desvios[coluna]) if not pd.isna(desvios[coluna]) else None
                direcao = "acima da media" if valor_analisado >= media else "abaixo da media"

                colunas_relevantes.append(
                    {
                        "coluna": coluna,
                        "valor_original": DetalhadorAnalise.serializar_valor(linha_original[coluna]),
                        "valor_analisado": DetalhadorAnalise.normalizar_numero(valor_analisado),
                        "score_coluna": DetalhadorAnalise.normalizar_numero(score_coluna, 4),
                        "direcao": direcao,
                        "media_referencia": DetalhadorAnalise.normalizar_numero(media),
                        "desvio_padrao_referencia": DetalhadorAnalise.normalizar_numero(desvio),
                        "limite_inferior": DetalhadorAnalise.normalizar_numero(media - threshold * desvio) if desvio is not None else None,
                        "limite_superior": DetalhadorAnalise.normalizar_numero(media + threshold * desvio) if desvio is not None else None,
                        "motivo": f"Valor {direcao} com Z-Score {score_coluna:.2f}, acima do limiar de {threshold:.2f}.",
                    }
                )

            if not colunas_relevantes:
                coluna_dominante = str(linha_z.idxmax())
                valor_analisado = float(linha_limpa[coluna_dominante])
                media = float(medias[coluna_dominante])
                desvio = float(desvios[coluna_dominante]) if not pd.isna(desvios[coluna_dominante]) else None
                score_coluna = float(linha_z[coluna_dominante])
                direcao = "acima da media" if valor_analisado >= media else "abaixo da media"
                colunas_relevantes.append(
                    {
                        "coluna": coluna_dominante,
                        "valor_original": DetalhadorAnalise.serializar_valor(linha_original[coluna_dominante]),
                        "valor_analisado": DetalhadorAnalise.normalizar_numero(valor_analisado),
                        "score_coluna": DetalhadorAnalise.normalizar_numero(score_coluna, 4),
                        "direcao": direcao,
                        "media_referencia": DetalhadorAnalise.normalizar_numero(media),
                        "desvio_padrao_referencia": DetalhadorAnalise.normalizar_numero(desvio),
                        "limite_inferior": DetalhadorAnalise.normalizar_numero(media - threshold * desvio) if desvio is not None else None,
                        "limite_superior": DetalhadorAnalise.normalizar_numero(media + threshold * desvio) if desvio is not None else None,
                        "motivo": f"Maior desvio observado na linha, com Z-Score {score_coluna:.2f}.",
                    }
                )

            colunas_relevantes.sort(key=lambda item: item.get("score_coluna") or 0.0, reverse=True)
            if len(colunas_relevantes) > 1:
                tipo_principal = "zscore_multicoluna"
            else:
                tipo_principal = (
                    "zscore_acima_limite_superior"
                    if colunas_relevantes[0]["direcao"] == "acima da media"
                    else "zscore_abaixo_limite_inferior"
                )

            detalhes.append(
                {
                    "indice_original": int(df_original.index[indice_posicional]) if str(df_original.index[indice_posicional]).isdigit() else indice_posicional,
                    "localizacao": DetalhadorAnalise.obter_localizacao_registro(indice_posicional, df_original.index[indice_posicional]),
                    "score": DetalhadorAnalise.normalizar_numero(scores_array[indice_posicional], 4),
                    "tipo_principal": tipo_principal,
                    "tipo_principal_nome": DetalhadorAnalise.CATALOGO_TIPOS_ANOMALIA[tipo_principal]["nome"],
                    "justificativa": (
                        f"Registro marcado porque {DetalhadorAnalise.compor_resumo_colunas_relevantes(colunas_relevantes)} "
                        f"ultrapassou o limiar de {threshold:.2f} desvios padrao."
                    ),
                    "dados_registro": DetalhadorAnalise.montar_dados_registro(df_original, indice_posicional, list(df_limpo.columns)),
                    "colunas_relevantes": colunas_relevantes,
                }
            )

        return sorted(detalhes, key=lambda item: item["score"] or 0.0, reverse=True)

    @staticmethod
    def construir_detalhes_iqr(
        df_original: pd.DataFrame,
        df_limpo: pd.DataFrame,
        flags_array: np.ndarray,
        scores_array: np.ndarray,
        parametros_utilizados: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Gera explicacoes detalhadas para anomalias detectadas via IQR.
        """
        fator = float(parametros_utilizados.get("fator", 1.5))
        q1 = df_limpo.quantile(0.25)
        q3 = df_limpo.quantile(0.75)
        iqr = q3 - q1
        limite_inferior = q1 - fator * iqr
        limite_superior = q3 + fator * iqr

        detalhes = []

        for indice_posicional, flag in enumerate(flags_array):
            if int(flag) != 1:
                continue

            linha_original = df_original.iloc[indice_posicional]
            linha_limpa = df_limpo.iloc[indice_posicional]
            colunas_relevantes = []

            for coluna in df_limpo.columns:
                valor = float(linha_limpa[coluna])
                if valor < float(limite_inferior[coluna]):
                    direcao = "abaixo do limite inferior"
                elif valor > float(limite_superior[coluna]):
                    direcao = "acima do limite superior"
                else:
                    continue

                distancia = float(limite_inferior[coluna] - valor) if direcao == "abaixo do limite inferior" else float(valor - limite_superior[coluna])
                colunas_relevantes.append(
                    {
                        "coluna": coluna,
                        "valor_original": DetalhadorAnalise.serializar_valor(linha_original[coluna]),
                        "valor_analisado": DetalhadorAnalise.normalizar_numero(valor),
                        "score_coluna": DetalhadorAnalise.normalizar_numero(distancia, 4),
                        "direcao": direcao,
                        "q1_referencia": DetalhadorAnalise.normalizar_numero(q1[coluna]),
                        "q3_referencia": DetalhadorAnalise.normalizar_numero(q3[coluna]),
                        "iqr_referencia": DetalhadorAnalise.normalizar_numero(iqr[coluna]),
                        "limite_inferior": DetalhadorAnalise.normalizar_numero(limite_inferior[coluna]),
                        "limite_superior": DetalhadorAnalise.normalizar_numero(limite_superior[coluna]),
                        "motivo": f"Valor {direcao} calculado por Q1/Q3 com fator {fator:.2f}.",
                    }
                )

            colunas_relevantes.sort(key=lambda item: item.get("score_coluna") or 0.0, reverse=True)
            if len(colunas_relevantes) > 1:
                tipo_principal = "iqr_multicoluna"
            else:
                tipo_principal = (
                    "iqr_acima_limite_superior"
                    if colunas_relevantes[0]["direcao"] == "acima do limite superior"
                    else "iqr_abaixo_limite_inferior"
                )

            detalhes.append(
                {
                    "indice_original": int(df_original.index[indice_posicional]) if str(df_original.index[indice_posicional]).isdigit() else indice_posicional,
                    "localizacao": DetalhadorAnalise.obter_localizacao_registro(indice_posicional, df_original.index[indice_posicional]),
                    "score": DetalhadorAnalise.normalizar_numero(scores_array[indice_posicional], 4),
                    "tipo_principal": tipo_principal,
                    "tipo_principal_nome": DetalhadorAnalise.CATALOGO_TIPOS_ANOMALIA[tipo_principal]["nome"],
                    "justificativa": (
                        f"Registro marcado porque {DetalhadorAnalise.compor_resumo_colunas_relevantes(colunas_relevantes)} "
                        f"ficou fora dos limites interquartis."
                    ),
                    "dados_registro": DetalhadorAnalise.montar_dados_registro(df_original, indice_posicional, list(df_limpo.columns)),
                    "colunas_relevantes": colunas_relevantes,
                }
            )

        return sorted(detalhes, key=lambda item: item["score"] or 0.0, reverse=True)

    @staticmethod
    def calcular_desvios_robustos(df_limpo: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Calcula referencias robustas usadas para explicar modelos baseados em densidade e isolamento.
        """
        medianas = df_limpo.median()
        q1 = df_limpo.quantile(0.25)
        q3 = df_limpo.quantile(0.75)
        iqr = q3 - q1
        desvios_padrao = df_limpo.std(ddof=0)
        escala = iqr.copy()
        escala[escala <= 0] = desvios_padrao[escala <= 0]
        escala[escala <= 0] = 1.0
        return medianas, q1, q3, escala

    @staticmethod
    def construir_detalhes_modelo_ml(
        algoritmo: str,
        df_original: pd.DataFrame,
        df_limpo: pd.DataFrame,
        flags_array: np.ndarray,
        scores_array: np.ndarray,
        parametros_utilizados: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Gera explicacoes detalhadas para algoritmos baseados em densidade e isolamento.
        """
        medianas, q1, q3, escala = DetalhadorAnalise.calcular_desvios_robustos(df_limpo)
        desvios_normalizados = ((df_limpo - medianas).abs().divide(escala)).replace([np.inf, -np.inf], np.nan).fillna(0.0)

        detalhes = []

        for indice_posicional, flag in enumerate(flags_array):
            if int(flag) != 1:
                continue

            linha_original = df_original.iloc[indice_posicional]
            linha_limpa = df_limpo.iloc[indice_posicional]
            contribuicoes = desvios_normalizados.iloc[indice_posicional].sort_values(ascending=False)
            colunas_relevantes = []

            for coluna, score_coluna in contribuicoes.items():
                colunas_relevantes.append(
                    {
                        "coluna": str(coluna),
                        "valor_original": DetalhadorAnalise.serializar_valor(linha_original[str(coluna)]),
                        "valor_analisado": DetalhadorAnalise.normalizar_numero(linha_limpa[str(coluna)]),
                        "score_coluna": DetalhadorAnalise.normalizar_numero(score_coluna, 4),
                        "mediana_referencia": DetalhadorAnalise.normalizar_numero(medianas[str(coluna)]),
                        "q1_referencia": DetalhadorAnalise.normalizar_numero(q1[str(coluna)]),
                        "q3_referencia": DetalhadorAnalise.normalizar_numero(q3[str(coluna)]),
                        "escala_referencia": DetalhadorAnalise.normalizar_numero(escala[str(coluna)]),
                        "motivo": (
                            "Coluna com alta contribuicao para o afastamento do comportamento central "
                            "observado pelo modelo."
                        ),
                    }
                )
                if len(colunas_relevantes) >= 3:
                    break

            score_top_1 = colunas_relevantes[0]["score_coluna"] or 0.0
            score_top_2 = colunas_relevantes[1]["score_coluna"] if len(colunas_relevantes) > 1 else 0.0
            desvio_dominante = bool(score_top_1 >= 1.5 and score_top_1 > score_top_2 * 1.35)

            if algoritmo == "isolation_forest":
                tipo_principal = (
                    "isolation_forest_desvio_dominante"
                    if desvio_dominante
                    else "isolation_forest_combinacao_rara"
                )
                justificativa = (
                    f"O Isolation Forest considerou este registro raro porque "
                    f"{DetalhadorAnalise.compor_resumo_colunas_relevantes(colunas_relevantes)} "
                    f"o afastou do padrao predominante."
                )
            else:
                tipo_principal = "lof_desvio_dominante" if desvio_dominante else "lof_combinacao_atipica"
                n_vizinhos = int(parametros_utilizados.get("n_vizinhos", 20))
                justificativa = (
                    f"O LOF marcou este registro por baixa densidade local em comparacao com {n_vizinhos} vizinhos, "
                    f"principalmente por causa de {DetalhadorAnalise.compor_resumo_colunas_relevantes(colunas_relevantes)}."
                )

            detalhes.append(
                {
                    "indice_original": int(df_original.index[indice_posicional]) if str(df_original.index[indice_posicional]).isdigit() else indice_posicional,
                    "localizacao": DetalhadorAnalise.obter_localizacao_registro(indice_posicional, df_original.index[indice_posicional]),
                    "score": DetalhadorAnalise.normalizar_numero(scores_array[indice_posicional], 4),
                    "tipo_principal": tipo_principal,
                    "tipo_principal_nome": DetalhadorAnalise.CATALOGO_TIPOS_ANOMALIA[tipo_principal]["nome"],
                    "justificativa": justificativa,
                    "dados_registro": DetalhadorAnalise.montar_dados_registro(df_original, indice_posicional, list(df_limpo.columns)),
                    "colunas_relevantes": colunas_relevantes,
                }
            )

        return sorted(detalhes, key=lambda item: item["score"] or 0.0, reverse=True)

    @staticmethod
    def construir_detalhes_anomalias(
        algoritmo: str,
        df_original: pd.DataFrame,
        df_limpo: pd.DataFrame,
        flags_array: np.ndarray,
        scores_array: np.ndarray,
        parametros_utilizados: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Encaminha a construcao dos detalhes conforme o algoritmo executado.
        """
        if algoritmo == "zscore":
            return DetalhadorAnalise.construir_detalhes_zscore(
                df_original,
                df_limpo,
                flags_array,
                scores_array,
                parametros_utilizados,
            )

        if algoritmo == "iqr":
            return DetalhadorAnalise.construir_detalhes_iqr(
                df_original,
                df_limpo,
                flags_array,
                scores_array,
                parametros_utilizados,
            )

        return DetalhadorAnalise.construir_detalhes_modelo_ml(
            algoritmo,
            df_original,
            df_limpo,
            flags_array,
            scores_array,
            parametros_utilizados,
        )

    @staticmethod
    def construir_resultado_resumo(
        algoritmo: str,
        df_original: pd.DataFrame,
        df_limpo: pd.DataFrame,
        flags_array: np.ndarray,
        scores_array: np.ndarray,
        parametros_utilizados: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Consolida o resumo tecnico e descritivo que sera persistido com a analise.
        """
        total_registros = int(len(df_original))
        total_anomalias = int(np.sum(flags_array))
        percentual_anomalias = float((total_anomalias / total_registros) * 100) if total_registros else 0.0
        score_medio = float(np.mean(scores_array)) if len(scores_array) else 0.0
        score_maximo = float(np.max(scores_array)) if len(scores_array) else 0.0

        detalhes_anomalias = DetalhadorAnalise.construir_detalhes_anomalias(
            algoritmo,
            df_original,
            df_limpo,
            flags_array,
            scores_array,
            parametros_utilizados,
        )
        tipos_encontrados, dicionario_tipos = DetalhadorAnalise.construir_distribuicao_tipos(
            detalhes_anomalias,
            total_anomalias,
        )

        return {
            "total_registros": total_registros,
            "total_anomalias": total_anomalias,
            "percentual_anomalias": percentual_anomalias,
            "score_medio": score_medio,
            "score_maximo": score_maximo,
            "parametros_utilizados": parametros_utilizados,
            "interpretacao_geral": DetalhadorAnalise.gerar_interpretacao_geral(
                algoritmo,
                total_anomalias,
                percentual_anomalias,
                score_maximo,
                parametros_utilizados,
            ),
            "tipos_anomalia_encontrados": tipos_encontrados,
            "dicionario_tipos_anomalia": dicionario_tipos,
            "anomalias_detalhadas": detalhes_anomalias,
        }
