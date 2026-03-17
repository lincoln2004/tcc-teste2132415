import pandas as pd
import numpy as np
from typing import Any, Dict, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from app.algoritmos.interface_algoritmo import AlgoritmoDeteccao

class IsolationForestDeteccao(AlgoritmoDeteccao):
    """
    Implementação da detecção de anomalias baseada em Isolation Forest.
    Isola anomalias construindo árvores de decisão aleatórias.
    
    Premissas: Anomalias são raras e têm valores de atributos diferentes dos normais.
    Vantagens: Funciona bem em dados de alta dimensão e não assume distribuição.
    """
    
    def treinar_e_prever(self, dados: pd.DataFrame, parametros: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Treina o modelo de Isolation Forest e retorna as flags e scores de anomalia.
        """
        contaminacao = parametros.get("contaminacao", 0.05)
        n_estimadores = parametros.get("n_estimadores", 100)
        
        # Inicializa o modelo
        modelo = IsolationForest(
            n_estimators=n_estimadores,
            contamination=contaminacao,
            random_state=42,
            n_jobs=-1
        )
        
        # Treina e prevê: 1 para normal, -1 para anomalia
        predicoes = modelo.fit_predict(dados)
        
        # Converte para o nosso padrão: 1 para anomalia, 0 para normal
        flags = (predicoes == -1).astype(int)
        
        # Obtém o score de anomalia (quanto menor, mais anômalo no sklearn)
        # Invertemos para que maior seja mais anômalo
        scores = -modelo.decision_function(dados)
        
        return flags, scores

    def obter_metadados(self) -> Dict[str, Any]:
        return {
            "nome": "Isolation Forest",
            "tipo": "machine_learning",
            "descricao": "Isola anomalias construindo árvores aleatórias.",
            "parametros_suportados": ["contaminacao", "n_estimadores"]
        }

class LocalOutlierFactorDeteccao(AlgoritmoDeteccao):
    """
    Implementação da detecção de anomalias baseada em Local Outlier Factor (LOF).
    Mede o desvio de densidade local de um dado em relação aos seus vizinhos.
    
    Premissas: Anomalias têm densidade local significativamente menor que seus vizinhos.
    Vantagens: Eficaz para detectar anomalias locais em clusters de densidades diferentes.
    """
    
    def treinar_e_prever(self, dados: pd.DataFrame, parametros: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula o LOF para cada registro e identifica anomalias.
        """
        contaminacao = parametros.get("contaminacao", 0.05)
        n_vizinhos = parametros.get("n_vizinhos", 20)
        
        # Inicializa o modelo
        modelo = LocalOutlierFactor(
            n_neighbors=n_vizinhos,
            contamination=contaminacao,
            n_jobs=-1
        )
        
        # Prevê: 1 para normal, -1 para anomalia
        predicoes = modelo.fit_predict(dados)
        
        # Converte para o nosso padrão: 1 para anomalia, 0 para normal
        flags = (predicoes == -1).astype(int)
        
        # Obtém o score de anomalia (quanto maior, mais anômalo no sklearn LOF)
        scores = -modelo.negative_outlier_factor_
        
        return flags, scores

    def obter_metadados(self) -> Dict[str, Any]:
        return {
            "nome": "Local Outlier Factor (LOF)",
            "tipo": "machine_learning",
            "descricao": "Mede o desvio de densidade local em relação aos vizinhos.",
            "parametros_suportados": ["contaminacao", "n_vizinhos"]
        }
