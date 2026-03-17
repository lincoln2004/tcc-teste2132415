/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from './api';
import { Analise, CriarAnaliseInput } from '../tipos';

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
};
