/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  ArrowLeft,
  FileText,
  Download,
  Loader2,
  AlertCircle,
  CheckCircle,
  FileUp,
  Info,
} from 'lucide-react';
import { analiseServico } from '../../servicos/analiseServico';
import { extrairMensagemErroApi } from '../../servicos/api';
import { TipoRelatorio } from '../../tipos';

const GerarRelatorios: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [relatorioSelecionado, setRelatorioSelecionado] = useState<string>('');
  const [formatoSaida, setFormatoSaida] = useState<string>('html');

  const { data: analise, isLoading: carregandoAnalise } = useQuery({
    queryKey: ['analise', id],
    queryFn: () => analiseServico.obterPorId(parseInt(id!, 10)),
    enabled: !!id,
  });

  const { data: tiposRelatorios, isLoading: carregandoTipos } = useQuery({
    queryKey: ['tipos-relatorios'],
    queryFn: analiseServico.listarTiposRelatorios,
  });

  const mutationGerar = useMutation({
    mutationFn: ({ tipo, formato }: { tipo: string; formato: string }) =>
      analiseServico.gerarRelatorio(parseInt(id!, 10), tipo, formato),
    onSuccess: () => {
      // Após gerar, baixar o relatorio
      if (relatorioSelecionado) {
        analiseServico.baixarRelatorio(parseInt(id!, 10), relatorioSelecionado);
      }
    },
  });

  const handleGerarRelatorio = () => {
    if (!relatorioSelecionado || !id) return;

    mutationGerar.mutate({
      tipo: relatorioSelecionado,
      formato: formatoSaida,
    });
  };

  if (carregandoAnalise || carregandoTipos) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center gap-4">
        <Loader2 className="w-12 h-12 text-emerald-500 animate-spin" />
        <div className="text-center">
          <h2 className="text-xl font-bold text-slate-900">Carregando...</h2>
          <p className="text-slate-500 text-sm mt-1">Estamos preparando as opcoes de relatorio.</p>
        </div>
      </div>
    );
  }

  if (!analise) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center gap-4 text-center">
        <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center">
          <AlertCircle className="w-8 h-8" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900">Analise nao encontrada</h2>
          <p className="text-slate-500 text-sm mt-1">Não foi possível recuperar esta analise.</p>
        </div>
        <Link to="/historico" className="text-emerald-600 font-bold hover:underline flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Voltar para o historico
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(`/analise/resultado/${id}`)}
          className="p-2 hover:bg-slate-100 rounded-xl transition-colors text-slate-400"
        >
          <ArrowLeft className="w-6 h-6" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Gerar Relatorio Especializado</h1>
          <p className="text-slate-500 mt-1">
            Escolha uma biblioteca especializada para gerar um relatorio detalhado dos dados tratados.
          </p>
        </div>
      </div>

      <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-200 space-y-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center">
            <FileText className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Selecionar Tipo de Relatorio</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {tiposRelatorios?.map((tipo) => (
            <button
              key={tipo.id}
              onClick={() => setRelatorioSelecionado(tipo.id)}
              className={`p-5 rounded-2xl border-2 text-left transition-all ${
                relatorioSelecionado === tipo.id
                  ? 'border-blue-500 bg-blue-50/50 ring-4 ring-blue-500/10'
                  : 'border-slate-100 hover:border-slate-200 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold text-slate-900">{tipo.nome}</span>
                {relatorioSelecionado === tipo.id && (
                  <CheckCircle className="w-5 h-5 text-blue-500" />
                )}
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">{tipo.descricao}</p>
            </button>
          ))}
        </div>

        <div className="space-y-4 pt-6 border-t border-slate-200">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700">Formato de Saida</label>
            <div className="flex gap-3">
              <button
                onClick={() => setFormatoSaida('html')}
                className={`px-4 py-2 rounded-xl border-2 text-sm font-bold transition-all ${
                  formatoSaida === 'html'
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                    : 'border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
              >
                HTML
              </button>
              <button
                onClick={() => setFormatoSaida('pdf')}
                disabled
                className="px-4 py-2 rounded-xl border-2 text-sm font-bold transition-all border-slate-200 text-slate-400 cursor-not-allowed opacity-50"
                title="PDF sera suportado em breve"
              >
                PDF (Em breve)
              </button>
            </div>
            <p className="text-xs text-slate-500 flex items-center gap-2">
              <Info className="w-3 h-3" />
              O formato HTML e interativo e pode ser visualizado em qualquer navegador.
            </p>
          </div>
        </div>

        {mutationGerar.isError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{extrairMensagemErroApi(mutationGerar.error, 'Erro ao gerar relatorio.')}</span>
          </div>
        )}

        {mutationGerar.isSuccess && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-700 text-sm flex items-start gap-3">
            <CheckCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>Relatorio gerado com sucesso! O download deve iniciar automaticamente.</span>
          </div>
        )}

        <div className="pt-6">
          <button
            onClick={handleGerarRelatorio}
            disabled={
              mutationGerar.isPending ||
              !relatorioSelecionado ||
              analise.status !== 'concluido'
            }
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-2xl shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mutationGerar.isPending ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" /> Gerando relatorio...
              </>
            ) : (
              <>
                <FileUp className="w-5 h-5" /> Gerar e Baixar Relatorio
              </>
            )}
          </button>
        </div>
      </div>

      <div className="bg-slate-50 p-6 rounded-3xl border border-slate-200">
        <h3 className="text-sm font-bold text-slate-900 mb-3">Sobre os relatorios especializados</h3>
        <div className="space-y-3 text-xs text-slate-600">
          <p>
            <strong className="text-slate-900">PyCaret:</strong> Biblioteca de machine learning automatizado que
            fornece analises estatisticas avancadas e deteccao de anomalias.
          </p>
          <p>
            <strong className="text-slate-900">DeepChecks:</strong> Suite completa de testes de integridade e
            qualidade de dados, ideal para validacao de datasets.
          </p>
          <p>
            <strong className="text-slate-900">Sweetviz:</strong> Gera relatorios exploratorios visuais e
            interativos com graficos automaticos.
          </p>
          <p>
            <strong className="text-slate-900">YData-Profiling:</strong> Cria perfis detalhados dos dados com
            estatisticas descritivas completas e correlacoes.
          </p>
        </div>
      </div>

      <div className="pt-4 flex items-center justify-between">
        <Link
          to={`/analise/${id}/dados-tratados`}
          className="text-emerald-600 font-bold hover:underline flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" /> Ver Dados Tratados
        </Link>
        <Link
          to={`/analise/resultado/${id}`}
          className="text-slate-600 font-bold hover:underline flex items-center gap-2"
        >
          Voltar ao Resultado <ArrowLeft className="w-4 h-4 rotate-180" />
        </Link>
      </div>
    </div>
  );
};

export default GerarRelatorios;
