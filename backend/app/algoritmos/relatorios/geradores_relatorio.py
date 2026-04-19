"""
Modulo de geracao de relatorios de anomalias usando bibliotecas especializadas.
Suporta: PyCaret, DeepChecks, Sweetviz e YData-Profiling.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

import pandas as pd


class GeradorRelatorio(ABC):
    """Interface base para geradores de relatorio."""

    @abstractmethod
    def gerar_relatorio(self, df: pd.DataFrame, caminho_saida: str) -> str:
        """Gera o relatorio e retorna o caminho do arquivo gerado."""
        pass

    @abstractmethod
    def obter_nome(self) -> str:
        """Retorna o nome do relatorio."""
        pass


class RelatorioPyCaret(GeradorRelatorio):
    """Gerador de relatorio usando PyCaret."""

    def obter_nome(self) -> str:
        return "PyCaret"

    def gerar_relatorio(self, df: pd.DataFrame, caminho_saida: str) -> str:
        try:
            from pycaret.anomaly import setup, create_model, plot_model, evaluate_model
            
            # Configurar o ambiente PyCaret
            modelo_analise = setup(data=df, silent=True, html=True)
            
            # Criar modelo de deteccao de anomalias (Isolation Forest por padrao)
            modelo = create_model('iforest')
            
            # Avaliar o modelo
            evaluate_model(modelo)
            
            # Salvar plot
            caminho_plot = caminho_saida.replace('.html', '_pycaret.png')
            plot_model(modelo, plot='tsne', save=True)
            
            # Para HTML, vamos criar um resumo simples pois PyCaret nao gera HTML direto
            self._gerar_html_resumo(df, modelo, caminho_saida)
            
            return caminho_saida
        except ImportError:
            raise RuntimeError("PyCaret nao esta instalado. Execute: pip install pycaret")
        except Exception as erro:
            raise RuntimeError(f"Erro ao gerar relatorio PyCaret: {erro}")
    
    def _gerar_html_resumo(self, df: pd.DataFrame, modelo: Any, caminho_saida: str) -> None:
        """Gera um HTML com resumo da analise PyCaret."""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Relatorio PyCaret - Analise de Anomalias</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
                h2 {{ color: #666; margin-top: 30px; }}
                .stat {{ display: inline-block; margin: 10px; padding: 15px; background: #e8f5e9; border-radius: 8px; min-width: 150px; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #2e7d32; }}
                .stat-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #4CAF50; color: white; }}
                tr:hover {{ background: #f5f5f5; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔍 Relatorio PyCaret - Analise de Anomalias</h1>
                
                <h2>Resumo do Dataset</h2>
                <div>
                    <div class="stat">
                        <div class="stat-value">{len(df)}</div>
                        <div class="stat-label">Registros</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{len(df.columns)}</div>
                        <div class="stat-label">Colunas</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{df.select_dtypes(include=['float64', 'int64']).shape[1]}</div>
                        <div class="stat-label">Colunas Numericas</div>
                    </div>
                </div>
                
                <h2>Estatisticas Descritivas</h2>
                <table>
                    <tr>
                        <th>Coluna</th>
                        <th>Media</th>
                        <th>Desvio Padrao</th>
                        <th>Minimo</th>
                        <th>Maximo</th>
                    </tr>
        """
        
        for col in df.select_dtypes(include=['float64', 'int64']).columns[:10]:
            html_content += f"""
                    <tr>
                        <td>{col}</td>
                        <td>{df[col].mean():.4f}</td>
                        <td>{df[col].std():.4f}</td>
                        <td>{df[col].min():.4f}</td>
                        <td>{df[col].max():.4f}</td>
                    </tr>
            """
        
        html_content += """
                </table>
                
                <h2>Informacoes do Modelo</h2>
                <p>O modelo Isolation Forest foi aplicado para deteccao de anomalias.</p>
                <p><strong>Observacao:</strong> Para visualizacao completa dos graficos, execute a analise em ambiente Jupyter Notebook.</p>
            </div>
        </body>
        </html>
        """
        
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.write(html_content)


class RelatorioDeepChecks(GeradorRelatorio):
    """Gerador de relatorio usando DeepChecks."""

    def obter_nome(self) -> str:
        return "DeepChecks"

    def gerar_relatorio(self, df: pd.DataFrame, caminho_saida: str) -> str:
        try:
            from deepchecks.tabular import Dataset, Suite
            from deepchecks.tabular.suites import data_integrity
            
            # Criar dataset DeepChecks
            dataset = Dataset(df=df)
            
            # Executar suite de integridade de dados
            suite = data_integrity()
            resultado = suite.run(dataset)
            
            # Salvar relatorio em HTML
            resultado.save_as_html(caminho_saida)
            
            return caminho_saida
        except ImportError:
            raise RuntimeError("DeepChecks nao esta instalado. Execute: pip install deepchecks")
        except Exception as erro:
            raise RuntimeError(f"Erro ao gerar relatorio DeepChecks: {erro}")


class RelatorioSweetviz(GeradorRelatorio):
    """Gerador de relatorio usando Sweetviz."""

    def obter_nome(self) -> str:
        return "Sweetviz"

    def gerar_relatorio(self, df: pd.DataFrame, caminho_saida: str) -> str:
        try:
            import sweetviz as sv
            
            # Criar relatorio exploratorio
            relatorio = sv.analyze(df)
            
            # Salvar em HTML
            relatorio.show_html(filepath=caminho_saida, open_browser=False)
            
            return caminho_saida
        except ImportError:
            raise RuntimeError("Sweetviz nao esta instalado. Execute: pip install sweetviz")
        except Exception as erro:
            raise RuntimeError(f"Erro ao gerar relatorio Sweetviz: {erro}")


class RelatorioYDataProfiling(GeradorRelatorio):
    """Gerador de relatorio usando YData-Profiling (antigo Pandas-Profiling)."""

    def obter_nome(self) -> str:
        return "YData-Profiling"

    def gerar_relatorio(self, df: pd.DataFrame, caminho_saida: str) -> str:
        try:
            from ydata_profiling import ProfileReport
            
            # Criar perfil dos dados
            perfil = ProfileReport(
                df,
                title="Relatorio de Analise Exploratoria",
                explorative=True,
                minimal=False,
                progress_bar=False
            )
            
            # Salvar em HTML
            perfil.to_file(caminho_saida)
            
            return caminho_saida
        except ImportError:
            raise RuntimeError("YData-Profiling nao esta instalado. Execute: pip install ydata-profiling")
        except Exception as erro:
            raise RuntimeError(f"Erro ao gerar relatorio YData-Profiling: {erro}")


class FabricaRelatorios:
    """Fabrica para criar instancias de geradores de relatorio."""
    
    GERADORES = {
        'pycaret': RelatorioPyCaret,
        'deepchecks': RelatorioDeepChecks,
        'sweetviz': RelatorioSweetviz,
        'ydata_profiling': RelatorioYDataProfiling,
    }
    
    @classmethod
    def obter_gerador(cls, tipo: str) -> GeradorRelatorio:
        """Retorna uma instancia do gerador solicitado."""
        if tipo not in cls.GERADORES:
            raise ValueError(f"Tipo de relatorio '{tipo}' nao suportado. Opcoes: {list(cls.GERADORES.keys())}")
        return cls.GERADORES[tipo]()
    
    @classmethod
    def listar_tipos(cls) -> list[str]:
        """Retorna lista de tipos de relatorios disponiveis."""
        return list(cls.GERADORES.keys())
