import csv
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


class ProcessadorDados:
    """
    Classe responsavel pelo pre-processamento dos datasets.
    Garante que os dados estejam limpos e normalizados para os algoritmos.
    """

    CODIFICACOES_TENTADAS = ("utf-8", "utf-8-sig", "latin1", "cp1252")
    SEPARADORES_SUPORTADOS = (",", ";", "\t", "|")
    TAXA_MINIMA_CONVERSAO_NUMERICA = 0.5

    @staticmethod
    def carregar_arquivo(caminho: str, formato: str) -> pd.DataFrame:
        """
        Carrega o arquivo fisico para um DataFrame do Pandas.
        """
        dataframe, _ = ProcessadorDados.carregar_arquivo_com_relatorio(caminho, formato)
        return dataframe

    @staticmethod
    def carregar_arquivo_com_relatorio(caminho: str, formato: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Carrega o arquivo e retorna tambem um relatorio de importacao util para o upload.
        """
        formato_normalizado = formato.lower()

        if formato_normalizado == "csv":
            return ProcessadorDados._carregar_csv_com_relatorio(caminho)

        if formato_normalizado in ["xlsx", "xls"]:
            dataframe = pd.read_excel(caminho)
            if dataframe.empty:
                raise ValueError("O arquivo enviado nao possui linhas de dados validas para importacao.")

            return dataframe, {
                "codificacao": None,
                "separador": None,
                "linhas_descartadas": 0,
                "linhas_com_problema": [],
            }

        raise ValueError(f"Formato de arquivo nao suportado: {formato}")

    @staticmethod
    def _carregar_csv_com_relatorio(caminho: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Carrega um CSV com tolerancia a linhas malformadas e registra o que foi descartado.
        """
        codificacao = ProcessadorDados._detectar_codificacao_csv(caminho)
        separador = ProcessadorDados._detectar_separador_csv(caminho, codificacao)
        linhas_com_problema = ProcessadorDados._identificar_linhas_malformadas_csv(
            caminho,
            codificacao,
            separador,
        )

        dataframe = pd.read_csv(
            caminho,
            sep=separador,
            encoding=codificacao,
            engine="python",
            on_bad_lines="skip",
            skipinitialspace=True,
        )
        dataframe.columns = [str(coluna).strip() for coluna in dataframe.columns]

        if dataframe.empty:
            raise ValueError("O arquivo enviado nao possui linhas de dados validas para importacao.")

        relatorio = {
            "codificacao": codificacao,
            "separador": separador,
            "linhas_descartadas": len(linhas_com_problema),
            "linhas_com_problema": linhas_com_problema,
        }

        if linhas_com_problema:
            relatorio["aviso_importacao"] = (
                f"Foram descartadas {len(linhas_com_problema)} linha(s) com formato inconsistente "
                f"durante a importacao do CSV: {', '.join(str(linha) for linha in linhas_com_problema)}."
            )

        return dataframe, relatorio

    @staticmethod
    def _detectar_codificacao_csv(caminho: str) -> str:
        """
        Detecta uma codificacao legivel para o CSV antes de iniciar a importacao.
        """
        arquivo = Path(caminho)

        for codificacao in ProcessadorDados.CODIFICACOES_TENTADAS:
            try:
                with arquivo.open("r", encoding=codificacao, newline="") as arquivo_texto:
                    arquivo_texto.read(4096)
                return codificacao
            except UnicodeDecodeError:
                continue

        raise ValueError("Nao foi possivel identificar a codificacao do arquivo CSV enviado.")

    @staticmethod
    def _detectar_separador_csv(caminho: str, codificacao: str) -> str:
        """
        Detecta o separador mais provavel do CSV a partir de uma pequena amostra do arquivo.
        """
        with Path(caminho).open("r", encoding=codificacao, newline="") as arquivo_csv:
            amostra = arquivo_csv.read(8192)

        linhas_utilizadas = [linha for linha in amostra.splitlines() if linha.strip()]
        if not linhas_utilizadas:
            raise ValueError("O arquivo CSV enviado esta vazio.")

        amostra_normalizada = "\n".join(linhas_utilizadas[:5])

        try:
            dialeto = csv.Sniffer().sniff(amostra_normalizada, delimiters=ProcessadorDados.SEPARADORES_SUPORTADOS)
            return dialeto.delimiter
        except csv.Error:
            contagens = {
                separador: amostra_normalizada.count(separador)
                for separador in ProcessadorDados.SEPARADORES_SUPORTADOS
            }
            separador_mais_frequente = max(contagens, key=contagens.get)
            return separador_mais_frequente if contagens[separador_mais_frequente] > 0 else ","

    @staticmethod
    def _identificar_linhas_malformadas_csv(caminho: str, codificacao: str, separador: str) -> List[int]:
        """
        Varre o CSV para identificar linhas cujo numero de campos diverge do cabecalho.
        """
        linhas_com_problema: List[int] = []

        with Path(caminho).open("r", encoding=codificacao, newline="") as arquivo_csv:
            leitor = csv.reader(arquivo_csv, delimiter=separador)
            cabecalho = next(leitor, None)

            if cabecalho is None:
                raise ValueError("O arquivo CSV enviado esta vazio.")

            quantidade_campos_esperada = len(cabecalho)

            for numero_linha, linha in enumerate(leitor, start=2):
                if not linha or not any(str(celula).strip() for celula in linha):
                    continue

                if len(linha) != quantidade_campos_esperada:
                    linhas_com_problema.append(numero_linha)

        return linhas_com_problema

    @staticmethod
    def limpar_dados(df: pd.DataFrame, colunas: List[str]) -> pd.DataFrame:
        """
        Realiza a limpeza basica dos dados para analise:
        - Valida se as colunas existem.
        - Converte valores textuais numericos para float.
        - Trata valores nulos com a media da coluna.
        """
        colunas_inexistentes = [coluna for coluna in colunas if coluna not in df.columns]
        if colunas_inexistentes:
            raise ValueError(
                "As seguintes colunas nao foram encontradas no dataset: "
                f"{', '.join(colunas_inexistentes)}."
            )

        df_limpo = pd.DataFrame(index=df.index)
        colunas_invalidas: List[str] = []

        for coluna in colunas:
            serie_numerica, coluna_compativel = ProcessadorDados.converter_serie_para_numerica(df[coluna])
            quantidade_valores_validos = int(serie_numerica.notna().sum())

            if not coluna_compativel or quantidade_valores_validos < 2:
                colunas_invalidas.append(coluna)
                continue

            media_coluna = serie_numerica.mean()
            if pd.isna(media_coluna):
                colunas_invalidas.append(coluna)
                continue

            df_limpo[coluna] = serie_numerica.fillna(media_coluna).astype(float)

        if colunas_invalidas:
            raise ValueError(
                "As colunas selecionadas nao sao numericas ou nao puderam ser convertidas "
                f"para analise: {', '.join(colunas_invalidas)}."
            )

        if df_limpo.empty:
            raise ValueError("Nenhuma coluna numerica valida foi informada para a analise.")

        return df_limpo

    @staticmethod
    def normalizar_dados(df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica normalizacao Z-Score nos dados numericos.
        """
        scaler = StandardScaler()
        colunas = df.columns
        dados_normalizados = scaler.fit_transform(df)

        return pd.DataFrame(dados_normalizados, columns=colunas, index=df.index)

    @staticmethod
    def converter_serie_para_numerica(serie: pd.Series) -> Tuple[pd.Series, bool]:
        """
        Converte uma serie para numeros quando ela estiver em formato textual.
        """
        if pd.api.types.is_numeric_dtype(serie):
            serie_numerica = pd.to_numeric(serie, errors="coerce").astype(float)
        else:
            serie_numerica = serie.apply(ProcessadorDados._converter_valor_textual_para_float).astype(float)

        quantidade_validos_originais = int(serie.notna().sum())
        quantidade_convertidos = int(serie_numerica.notna().sum())

        if quantidade_validos_originais == 0:
            return serie_numerica, False

        taxa_conversao = quantidade_convertidos / quantidade_validos_originais
        coluna_compativel = (
            quantidade_convertidos >= 2
            and taxa_conversao >= ProcessadorDados.TAXA_MINIMA_CONVERSAO_NUMERICA
        )
        return serie_numerica, coluna_compativel

    @staticmethod
    def _converter_valor_textual_para_float(valor: Any) -> float:
        """
        Converte um valor textual numerico para float, aceitando moeda, espacos e virgula decimal.
        """
        if pd.isna(valor):
            return np.nan

        if isinstance(valor, (int, float, np.integer, np.floating)):
            return float(valor)

        texto = str(valor).strip()
        if not texto:
            return np.nan

        negativo_por_parenteses = texto.startswith("(") and texto.endswith(")")
        if negativo_por_parenteses:
            texto = texto[1:-1]

        texto_sem_prefixos = (
            texto.replace("R$", "")
            .replace("US$", "")
            .replace("USD", "")
            .replace("BRL", "")
            .replace("EUR", "")
        )
        if re.search(r"[A-Za-z]", texto_sem_prefixos):
            return np.nan

        texto = texto.replace("\xa0", "").replace(" ", "")
        texto = re.sub(r"[^0-9,.\-]", "", texto)

        if texto in {"", "-", ",", ".", "-.", "-,"}:
            return np.nan

        if "," in texto and "." in texto:
            if texto.rfind(",") > texto.rfind("."):
                texto = texto.replace(".", "").replace(",", ".")
            else:
                texto = texto.replace(",", "")
        elif "," in texto:
            texto = ProcessadorDados._normalizar_separador_unico(texto, ",")
        elif "." in texto:
            texto = ProcessadorDados._normalizar_separador_unico(texto, ".")

        try:
            numero = float(texto)
        except ValueError:
            return np.nan

        return -numero if negativo_por_parenteses else numero

    @staticmethod
    def _normalizar_separador_unico(texto: str, separador: str) -> str:
        """
        Resolve casos em que apenas um tipo de separador decimal ou milhar aparece no valor.
        """
        ocorrencias = texto.count(separador)

        if ocorrencias > 1:
            partes = texto.split(separador)
            if all(parte.isdigit() and len(parte) == 3 for parte in partes[1:]):
                return "".join(partes)
            return "".join(partes[:-1]) + "." + partes[-1]

        parte_inteira, parte_decimal = texto.split(separador)
        if parte_decimal.isdigit() and len(parte_decimal) == 3:
            return parte_inteira + parte_decimal
        return parte_inteira + "." + parte_decimal

    @staticmethod
    def extrair_metadados(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Extrai estatisticas basicas de cada coluna para exibicao no frontend.
        """
        metadados = []
        for coluna in df.columns:
            serie_numerica, coluna_compativel = ProcessadorDados.converter_serie_para_numerica(df[coluna])
            tipo_coluna = str(serie_numerica.dtype) if coluna_compativel else str(df[coluna].dtype)

            info = {
                "nome": coluna,
                "tipo": tipo_coluna,
                "valores_nulos": int(df[coluna].isnull().sum()),
                "percentual_nulos": float((df[coluna].isnull().sum() / len(df)) * 100),
                "estatisticas": {},
            }

            if coluna_compativel:
                info["estatisticas"] = {
                    "min": float(serie_numerica.min()),
                    "max": float(serie_numerica.max()),
                    "media": float(serie_numerica.mean()),
                    "mediana": float(serie_numerica.median()),
                    "desvio_padrao": float(serie_numerica.std()),
                }

            metadados.append(info)

        return metadados
