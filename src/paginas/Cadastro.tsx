/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus, Mail, Lock, User, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { authServico } from '../servicos/authServico';
import { extrairMensagemErroApi } from '../servicos/api';

const cadastroSchema = z
  .object({
    nome: z.string().trim().min(3, 'O nome deve ter no minimo 3 caracteres'),
    email: z.string().trim().toLowerCase().email('E-mail invalido'),
    senha: z
      .string()
      .trim()
      .min(8, 'A senha deve ter no minimo 8 caracteres')
      .refine((valor) => /[A-Za-z]/.test(valor), 'A senha deve conter ao menos uma letra')
      .refine((valor) => /\d/.test(valor), 'A senha deve conter ao menos um numero'),
    confirmarSenha: z.string().trim(),
  })
  .refine((data) => data.senha === data.confirmarSenha, {
    message: 'As senhas nao coincidem',
    path: ['confirmarSenha'],
  });

type CadastroFormData = z.infer<typeof cadastroSchema>;

const Cadastro: React.FC = () => {
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState(false);
  const [carregando, setCarregando] = useState(false);
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CadastroFormData>({
    resolver: zodResolver(cadastroSchema),
  });

  /**
   * Envia os dados do formulario para criar a conta e redireciona ao login em caso de sucesso.
   */
  const onSubmit = async (data: CadastroFormData) => {
    setCarregando(true);
    setErro(null);

    try {
      await authServico.cadastro(data.nome, data.email, data.senha);
      setSucesso(true);
      window.setTimeout(() => navigate('/login'), 3000);
    } catch (erroApi) {
      setErro(extrairMensagemErroApi(erroApi, 'Erro ao criar conta. Tente novamente.'));
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-3xl shadow-xl border border-slate-100">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 text-emerald-600 rounded-2xl mb-4">
            <UserPlus className="w-8 h-8" />
          </div>
          <h2 className="text-3xl font-bold text-slate-900 tracking-tight">Criar Conta</h2>
          <p className="text-slate-500 mt-2">Junte-se a plataforma de deteccao de anomalias.</p>
        </div>

        {sucesso ? (
          <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-2xl text-center space-y-4">
            <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto" />
            <h3 className="text-lg font-bold text-emerald-900">Conta criada com sucesso!</h3>
            <p className="text-emerald-700 text-sm">Voce sera redirecionado para o login em instantes...</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {erro && (
              <div className="p-4 bg-red-50 border border-red-200 text-red-600 text-sm rounded-xl flex items-center gap-3 font-medium">
                <AlertCircle className="w-5 h-5" /> {erro}
              </div>
            )}

            <div className="space-y-1">
              <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <User className="w-4 h-4" /> Nome Completo
              </label>
              <input
                {...register('nome')}
                type="text"
                placeholder="Seu nome"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
              />
              {errors.nome && <p className="text-xs text-red-500 font-medium">{errors.nome.message}</p>}
            </div>

            <div className="space-y-1">
              <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <Mail className="w-4 h-4" /> E-mail
              </label>
              <input
                {...register('email')}
                type="email"
                placeholder="seu@email.com"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
              />
              {errors.email && <p className="text-xs text-red-500 font-medium">{errors.email.message}</p>}
            </div>

            <div className="space-y-1">
              <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <Lock className="w-4 h-4" /> Senha
              </label>
              <input
                {...register('senha')}
                type="password"
                placeholder="********"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
              />
              {errors.senha && <p className="text-xs text-red-500 font-medium">{errors.senha.message}</p>}
            </div>

            <div className="space-y-1">
              <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <Lock className="w-4 h-4" /> Confirmar Senha
              </label>
              <input
                {...register('confirmarSenha')}
                type="password"
                placeholder="********"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
              />
              {errors.confirmarSenha && <p className="text-xs text-red-500 font-medium">{errors.confirmarSenha.message}</p>}
            </div>

            <button
              type="submit"
              disabled={carregando}
              className="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-4 rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-70"
            >
              {carregando ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Criar Minha Conta'}
            </button>

            <p className="text-center text-sm text-slate-500">
              Ja tem uma conta?{' '}
              <Link to="/login" className="text-emerald-600 font-bold hover:underline">
                Faca Login
              </Link>
            </p>
          </form>
        )}
      </div>
    </div>
  );
};

export default Cadastro;
