/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldAlert, Mail, Lock, ArrowRight, Loader2 } from 'lucide-react';
import { authServico } from '../servicos/authServico';
import { extrairMensagemErroApi } from '../servicos/api';
import { useAuth } from '../contextos/AuthContexto';

const loginSchema = z.object({
  email: z.string().trim().toLowerCase().email('E-mail invalido'),
  senha: z.string().min(8, 'A senha deve ter no minimo 8 caracteres'),
});

type LoginFormData = z.infer<typeof loginSchema>;

const Login: React.FC = () => {
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  /**
   * Envia as credenciais para a API e carrega o usuario autenticado na sessao.
   */
  const onSubmit = async (data: LoginFormData) => {
    setCarregando(true);
    setErro(null);

    try {
      const response = await authServico.login(data.email, data.senha);
      await login(response.access_token);
      navigate('/');
    } catch (erroApi) {
      setErro(extrairMensagemErroApi(erroApi, 'Erro ao realizar login. Verifique suas credenciais.'));
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden">
        <div className="p-8 bg-slate-900 text-white flex flex-col items-center gap-4">
          <div className="w-16 h-16 bg-emerald-500/20 rounded-2xl flex items-center justify-center border border-emerald-500/30">
            <ShieldAlert className="w-10 h-10 text-emerald-400" />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold tracking-tight">Bem-vindo de volta</h1>
            <p className="text-slate-400 text-sm mt-1">Acesse sua conta para gerenciar anomalias</p>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-8 space-y-6">
          {erro && (
            <div className="p-4 bg-red-50 border border-red-200 text-red-600 text-sm rounded-xl font-medium">
              {erro}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Mail className="w-4 h-4 text-slate-400" /> E-mail
            </label>
            <input
              {...register('email')}
              type="email"
              placeholder="seu@email.com"
              className={`w-full px-4 py-3 rounded-xl border ${errors.email ? 'border-red-500' : 'border-slate-200'} focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all`}
            />
            {errors.email && <p className="text-xs text-red-500 font-medium">{errors.email.message}</p>}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Lock className="w-4 h-4 text-slate-400" /> Senha
            </label>
            <input
              {...register('senha')}
              type="password"
              placeholder="********"
              className={`w-full px-4 py-3 rounded-xl border ${errors.senha ? 'border-red-500' : 'border-slate-200'} focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all`}
            />
            {errors.senha && <p className="text-xs text-red-500 font-medium">{errors.senha.message}</p>}
          </div>

          <button
            type="submit"
            disabled={carregando}
            className="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-3 rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-70"
          >
            {carregando ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                Entrar <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>

          <p className="text-center text-sm text-slate-500">
            Nao tem uma conta?{' '}
            <Link to="/cadastro" className="text-emerald-600 font-bold hover:underline">
              Cadastre-se
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Login;
