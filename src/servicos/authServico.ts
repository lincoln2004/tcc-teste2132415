/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from './api';
import { Token, Usuario } from '../tipos';

export const authServico = {
  /**
   * Realiza o login usando o formato esperado pelo fluxo OAuth2 do FastAPI.
   */
  async login(email: string, senha: string): Promise<Token> {
    const formulario = new URLSearchParams();
    formulario.append('username', email.trim().toLowerCase());
    formulario.append('password', senha);

    const response = await api.post<Token>('/auth/login', formulario, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    return response.data;
  },

  /**
   * Realiza o cadastro de um novo usuario.
   */
  async cadastro(nome: string, email: string, senha: string): Promise<Usuario> {
    const response = await api.post<Usuario>('/auth/cadastro', {
      nome: nome.trim(),
      email: email.trim().toLowerCase(),
      senha,
    });

    return response.data;
  },

  /**
   * Busca o usuario autenticado a partir do token armazenado no cliente.
   */
  async getUsuarioAtual(): Promise<Usuario> {
    const response = await api.get<Usuario>('/auth/me');
    return response.data;
  },
};
