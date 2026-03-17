import pandas as pd
import numpy as np
from typing import Any, Dict, Tuple
from scipy import stats
from app.algoritmos.interface_algoritmo import AlgoritmoDeteccao

class ZScoreDeteccao(AlgoritmoDeteccao):
    """
    Implementação da detecção de anomalias baseada em Z-Score.
    Calcula o desvio padrão de cada ponto em relação à média.
    
    Premissas: Os dados seguem uma distribuição aproximadamente normal.
    Limitações: Sensível a outliers extremos que podem distorcer a média.
    """
    
    def treinar_e_prever(self, dados: pd.DataFrame, parametros: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula o Z-Score para cada registro e identifica anomalias com base em um threshold.
        """
        threshold = parametros.get("threshold", 3.0)
        
        # Calcula o Z-Score absoluto para cada coluna e tira a média entre elas
        z_scores = np.abs(stats.zscore(dados))
        
        # Se houver múltiplas colunas, pegamos o máximo Z-Score entre elas para cada linha
        max_z_scores = np.max(z_scores, axis=1)
        
        # Flag de anomalia: 1 se o Z-Score ultrapassar o threshold, 0 caso contrário
        flags = (max_z_scores > threshold).astype(int)
        
        return flags, max_z_scores

    def obter_metadados(self) -> Dict[str, Any]:
        return {
            "nome": "Z-Score",
            "tipo": "estatistico",
            "descricao": "Detecta anomalias com base no desvio padrão em relação à média.",
            "parametros_suportados": ["threshold"]
        }

class IQRDeteccao(AlgoritmoDeteccao):
    """
    Implementação da detecção de anomalias baseada em Intervalo Interquartil (IQR).
    Identifica pontos fora dos 'limites' (Q1 - 1.5*IQR e Q3 + 1.5*IQR).
    
    Premissas: Não assume distribuição normal (mais robusto que Z-Score).
    Limitações: Pode falhar em dados com variabilidade extrema.
    """
    
    def treinar_e_prever(self, dados: pd.DataFrame, parametros: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula o IQR e identifica anomalias fora dos limites inferior e superior.
        """
        fator = parametros.get("fator", 1.5)
        
        q1 = dados.quantile(0.25)
        q3 = dados.quantile(0.75)
        iqr = q3 - q1
        
        limite_inferior = q1 - fator * iqr
        limite_superior = q3 + fator * iqr
        
        # Identifica se algum valor na linha está fora dos limites
        anomalias = (dados < limite_inferior) | (dados > limite_superior)
        flags = anomalias.any(axis=1).astype(int)
        
        # O score aqui pode ser a distância máxima em relação aos limites (normalizada)
        # Para simplificar, usaremos a contagem de colunas anômalas como score proporcional
        scores = anomalias.sum(axis=1).astype(float)
        
        return flags, scores

    def obter_metadados(self) -> Dict[str, Any]:
        return {
            "nome": "IQR (Interquartile Range)",
            "tipo": "estatistico",
            "descricao": "Detecta anomalias com base na dispersão dos quartis centrais.",
            "parametros_suportados": ["fator"]
        }
