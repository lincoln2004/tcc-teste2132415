/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { Usuario } from '../tipos';
import { authServico } from '../servicos/authServico';

interface AuthContextType {
  usuario: Usuario | null;
  estaAutenticado: boolean;
  carregando: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregando, setCarregando] = useState(true);

  /**
   * Carrega o usuario autenticado no backend usando o token salvo localmente.
   */
  const carregarUsuarioAtual = async (): Promise<Usuario> => {
    const usuarioAtual = await authServico.getUsuarioAtual();
    setUsuario(usuarioAtual);
    return usuarioAtual;
  };

  useEffect(() => {
    let ativo = true;

    /**
     * Restaura a sessao do usuario ao abrir a aplicacao.
     */
    const restaurarSessao = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        if (ativo) {
          setCarregando(false);
        }
        return;
      }

      try {
        const usuarioAtual = await authServico.getUsuarioAtual();
        if (ativo) {
          setUsuario(usuarioAtual);
        }
      } catch {
        localStorage.removeItem('token');
        if (ativo) {
          setUsuario(null);
        }
      } finally {
        if (ativo) {
          setCarregando(false);
        }
      }
    };

    restaurarSessao();

    return () => {
      ativo = false;
    };
  }, []);

  /**
   * Persiste o token de acesso e busca o usuario real autenticado.
   */
  const login = async (token: string) => {
    localStorage.setItem('token', token);

    try {
      await carregarUsuarioAtual();
    } catch (erro) {
      localStorage.removeItem('token');
      setUsuario(null);
      throw erro;
    }
  };

  /**
   * Encerra a sessao local do usuario e retorna para a tela de login.
   */
  const logout = () => {
    localStorage.removeItem('token');
    setUsuario(null);
    window.location.assign('/login');
  };

  return (
    <AuthContext.Provider value={{ usuario, estaAutenticado: !!usuario, carregando, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};
