/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from './api';
import { Dataset } from '../tipos';

export const datasetServico = {
  /**
   * Realiza o upload de um novo dataset (CSV/XLSX).
   */
  async upload(nome: string, descricao: string, arquivo: File): Promise<Dataset> {
    const formData = new FormData();
    formData.append('nome', nome);
    formData.append('descricao', descricao);
    formData.append('arquivo', arquivo);

    const response = await api.post<Dataset>('/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  /**
   * Lista todos os datasets do usuário logado.
   */
  async listar(): Promise<Dataset[]> {
    const response = await api.get<Dataset[]>('/datasets/');
    return response.data;
  },

  /**
   * Obtém os detalhes de um dataset específico.
   */
  async obterPorId(id: number): Promise<Dataset> {
    const response = await api.get<Dataset>(`/datasets/${id}`);
    return response.data;
  },

  /**
   * Exclui um dataset do usuario logado e remove seus artefatos relacionados.
   */
  async excluir(id: number): Promise<{ mensagem: string; dataset_id: number; analises_removidas: number }> {
    const response = await api.delete<{ mensagem: string; dataset_id: number; analises_removidas: number }>(
      `/datasets/${id}`
    );
    return response.data;
  },
};
