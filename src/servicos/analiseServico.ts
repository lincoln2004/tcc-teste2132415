/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from './api';
import { Analise, CriarAnaliseInput, TipoRelatorio } from '../tipos';

export const analiseServico = {
  /**
   * Dispara a execucao de uma nova analise.
   */
  async executar(dados: CriarAnaliseInput): Promise<Analise> {
    const response = await api.post<Analise>('/analises/executar', dados);
    return response.data;
  },

  /**
   * Lista o historico de analises do usuario logado.
   */
  async listarHistorico(): Promise<Analise[]> {
    const response = await api.get<Analise[]>('/analises/historico');
    return response.data;
  },

  /**
   * Exclui todo o historico de analises do usuario autenticado.
   */
  async excluirHistorico(): Promise<{ mensagem: string; analises_removidas: number }> {
    const response = await api.delete<{ mensagem: string; analises_removidas: number }>('/analises/historico');
    return response.data;
  },

  /**
   * Obtem os detalhes de uma analise especifica.
   */
  async obterPorId(id: number): Promise<Analise> {
    const response = await api.get<Analise>(`/analises/${id}`);
    return response.data;
  },

  /**
   * Baixa o CSV autenticado da analise concluida usando o token da sessao atual.
   */
  async baixarResultado(analiseId: number): Promise<void> {
    const response = await api.get<Blob>(`/analises/${analiseId}/download`, {
      responseType: 'blob',
    });

    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');

    link.href = url;
    link.download = `resultado_analise_${analiseId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  /**
   * Lista os tipos de relatorios disponiveis.
   */
  async listarTiposRelatorios(): Promise<TipoRelatorio[]> {
    const response = await api.get<{ tipos: TipoRelatorio[] }>('/analises/tipos-relatorios');
    return response.data.tipos;
  },

  /**
   * Gera um relatorio especializado para uma analise.
   */
  async gerarRelatorio(
    analiseId: number,
    tipoRelatorio: string,
    formatoSaida: string = 'html',
  ): Promise<{ mensagem: string; caminho_arquivo: string; tipo_relatorio: string; formato_saida: string }> {
    const response = await api.post<{
      mensagem: string;
      caminho_arquivo: string;
      tipo_relatorio: string;
      formato_saida: string;
    }>(`/analises/${analiseId}/gerar-relatorio`, null, {
      params: {
        tipo_relatorio: tipoRelatorio,
        formato_saida: formatoSaida,
      },
    });
    return response.data;
  },

  /**
   * Baixa um relatorio especializado em HTML.
   */
  async baixarRelatorio(analiseId: number, tipoRelatorio: string): Promise<void> {
    const response = await api.get<Blob>(`/analises/${analiseId}/baixar-relatorio`, {
      params: {
        tipo_relatorio: tipoRelatorio,
      },
      responseType: 'blob',
    });

    const blob = new Blob([response.data], { type: 'text/html;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');

    link.href = url;
    link.download = `relatorio_${tipoRelatorio}_analise_${analiseId}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
