from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
import pandas as pd
import numpy as np

class AlgoritmoDeteccao(ABC):
    """
    Interface abstrata para algoritmos de detecção de anomalias.
    Define o contrato obrigatório para qualquer novo método implementado.
    """
    
    @abstractmethod
    def treinar_e_prever(self, dados: pd.DataFrame, parametros: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Executa o treinamento (se necessário) e a predição de anomalias.
        
        Parâmetros:
            dados: DataFrame do Pandas com as colunas numéricas selecionadas.
            parametros: Dicionário com hiperparâmetros (ex: contaminação, threshold).
            
        Retorna:
            Uma tupla contendo:
            - Array de flags binárias (1 para anomalia, 0 para normal).
            - Array de scores de anomalia (quanto maior, mais anômalo).
        """
        pass

    @abstractmethod
    def obter_metadados(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o algoritmo (nome, tipo, limitações).
        """
        pass
