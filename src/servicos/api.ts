/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL?.trim() || '/api/v1';

/**
 * Extrai uma mensagem de erro amigavel a partir do formato retornado pela API.
 */
export function extrairMensagemErroApi(erro: unknown, mensagemPadrao: string): string {
  if (!axios.isAxiosError(erro)) {
    return mensagemPadrao;
  }

  const detalhe = erro.response?.data?.detail;

  if (typeof detalhe === 'string' && detalhe.trim()) {
    return detalhe;
  }

  if (Array.isArray(detalhe)) {
    const mensagens = detalhe
      .map((item) => {
        if (typeof item === 'string') {
          return item;
        }

        if (!item || typeof item !== 'object') {
          return '';
        }

        const campo = Array.isArray(item.loc)
          ? item.loc
              .filter((parte) => !['body', 'query', 'path'].includes(String(parte)))
              .join('.')
          : '';
        const mensagem = typeof item.msg === 'string' ? item.msg : '';

        if (campo && mensagem) {
          return `${campo}: ${mensagem}`;
        }

        return mensagem || campo;
      })
      .filter(Boolean);

    if (mensagens.length > 0) {
      return mensagens.join(' | ');
    }
  }

  const mensagem = erro.response?.data?.message;
  if (typeof mensagem === 'string' && mensagem.trim()) {
    return mensagem;
  }

  return erro.message || mensagemPadrao;
}

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (erro) => {
    const urlRequisicao = erro.config?.url ?? '';
    const deveRedirecionar =
      erro.response?.status === 401 &&
      !urlRequisicao.includes('/auth/login') &&
      !urlRequisicao.includes('/auth/cadastro');

    if (deveRedirecionar) {
      localStorage.removeItem('token');
      window.location.assign('/login');
    }

    return Promise.reject(erro);
  }
);
