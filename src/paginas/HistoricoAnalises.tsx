/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle,
  Clock,
  Download,
  Loader2,
  Search,
  Trash2,
} from 'lucide-react';
import ModalConfirmacaoExclusaoHistorico from '../componentes/analises/ModalConfirmacaoExclusaoHistorico';
import { analiseServico } from '../servicos/analiseServico';
import { extrairMensagemErroApi } from '../servicos/api';
import { Analise } from '../tipos';

const HistoricoAnalises: React.FC = () => {
  const queryClient = useQueryClient();
  const [termoBusca, setTermoBusca] = useState('');
  const [filtroStatus, setFiltroStatus] = useState('todos');
  const [filtroAlgoritmo, setFiltroAlgoritmo] = useState('todos');
  const [analiseBaixandoId, setAnaliseBaixandoId] = useState<number | null>(null);
  const [erroAcao, setErroAcao] = useState<string | null>(null);
  const [mensagemAcao, setMensagemAcao] = useState<string | null>(null);
  const [modalExclusaoAberto, setModalExclusaoAberto] = useState(false);

  const { data: historico, isLoading, error } = useQuery({
    queryKey: ['historico'],
    queryFn: analiseServico.listarHistorico,
  });

  /**
   * Exclui todas as analises do historico e limpa os caches derivados do frontend.
   */
  const exclusaoHistoricoMutation = useMutation({
    mutationFn: () => analiseServico.excluirHistorico(),
    onSuccess: (resultado) => {
      queryClient.setQueryData<Analise[]>(['historico'], []);
      queryClient.removeQueries({ queryKey: ['analise'] });
      void queryClient.invalidateQueries({ queryKey: ['historico'] });

      setErroAcao(null);
      setModalExclusaoAberto(false);
      setMensagemAcao(
        resultado.analises_removidas > 0
          ? `${resultado.mensagem} ${resultado.analises_removidas} analise(s) foram removidas do armazenamento local.`
          : 'Nao havia analises salvas para excluir.'
      );
    },
    onError: (erroApi) => {
      setMensagemAcao(null);
      setErroAcao(extrairMensagemErroApi(erroApi, 'Nao foi possivel excluir o historico de analises.'));
    },
  });

  /**
   * Traduz o identificador tecnico do algoritmo para um nome mais claro na interface.
   */
  const formatarAlgoritmo = (algoritmo: string) => {
    const nomes: Record<string, string> = {
      zscore: 'Z-Score',
      iqr: 'IQR',
      isolation_forest: 'Isolation Forest',
      lof: 'LOF',
    };

    return nomes[algoritmo] || algoritmo;
  };

  /**
   * Retorna classes utilitarias para destacar visualmente o status da analise.
   */
  const obterEstiloStatus = (status: Analise['status']) => {
    if (status === 'concluido') {
      return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
    }

    if (status === 'erro') {
      return 'bg-red-50 text-red-700 border border-red-200';
    }

    return 'bg-amber-50 text-amber-700 border border-amber-200';
  };

  /**
   * Aplica os filtros de busca, status e algoritmo sobre o historico retornado pela API.
   */
  const analisesFiltradas = useMemo(() => {
    const termoNormalizado = termoBusca.trim().toLowerCase();

    return (historico ?? []).filter((analise) => {
      const correspondeTermo =
        !termoNormalizado ||
        [analise.nome, analise.algoritmo, analise.tipo_algoritmo]
          .some((valor) => valor.toLowerCase().includes(termoNormalizado));

      const correspondeStatus = filtroStatus === 'todos' || analise.status === filtroStatus;
      const correspondeAlgoritmo = filtroAlgoritmo === 'todos' || analise.algoritmo === filtroAlgoritmo;

      return correspondeTermo && correspondeStatus && correspondeAlgoritmo;
    });
  }, [filtroAlgoritmo, filtroStatus, historico, termoBusca]);

  /**
   * Baixa o CSV de resultado para uma analise concluida usando o token da sessao atual.
   */
  const baixarResultado = async (analise: Analise) => {
    try {
      setErroAcao(null);
      setAnaliseBaixandoId(analise.id);
      await analiseServico.baixarResultado(analise.id);
    } catch (erroApi) {
      setErroAcao(extrairMensagemErroApi(erroApi, 'Nao foi possivel baixar o CSV desta analise.'));
    } finally {
      setAnaliseBaixandoId(null);
    }
  };

  const totalAnalises = historico?.length ?? 0;
  const analisesConcluidas = historico?.filter((analise) => analise.status === 'concluido').length ?? 0;
  const analisesProcessando = historico?.filter((analise) => analise.status === 'processando').length ?? 0;
  const totalAnomalias =
    historico?.reduce(
      (acumulador, analise) => acumulador + (analise.resultado_resumo?.total_anomalias ?? 0),
      0
    ) ?? 0;
  const semResultadosComFiltro = !isLoading && totalAnalises > 0 && analisesFiltradas.length === 0;

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Historico de Analises</h1>
          <p className="text-slate-500 mt-1">Acompanhe as execucoes realizadas e reabra resultados anteriores.</p>
        </div>

        <button
          type="button"
          onClick={() => {
            setErroAcao(null);
            setMensagemAcao(null);
            setModalExclusaoAberto(true);
          }}
          disabled={totalAnalises === 0}
          className="inline-flex items-center gap-2 rounded-2xl bg-red-600 px-5 py-3 text-sm font-bold text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Trash2 className="w-4 h-4" />
          Excluir todo o historico
        </button>
      </div>

      {mensagemAcao && (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
          {mensagemAcao}
        </div>
      )}

      {(erroAcao || error) && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{erroAcao ?? extrairMensagemErroApi(error, 'Nao foi possivel carregar o historico de analises.')}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Total de analises</p>
          <p className="mt-3 text-3xl font-bold text-slate-900">{totalAnalises}</p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Concluidas</p>
          <p className="mt-3 text-3xl font-bold text-emerald-600">{analisesConcluidas}</p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Em processamento</p>
          <p className="mt-3 text-3xl font-bold text-amber-600">{analisesProcessando}</p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Anomalias encontradas</p>
          <p className="mt-3 text-3xl font-bold text-red-600">{totalAnomalias}</p>
        </div>
      </div>

      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_220px_220px] gap-4">
          <div className="flex items-center gap-3 bg-slate-50 px-4 py-3 rounded-2xl border border-slate-200">
            <Search className="w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={termoBusca}
              onChange={(evento) => setTermoBusca(evento.target.value)}
              placeholder="Buscar por nome, algoritmo ou tipo..."
              className="w-full bg-transparent text-sm text-slate-600 outline-none"
            />
          </div>

          <select
            value={filtroStatus}
            onChange={(evento) => setFiltroStatus(evento.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 outline-none focus:border-emerald-500"
          >
            <option value="todos">Todos os status</option>
            <option value="concluido">Concluidas</option>
            <option value="processando">Em processamento</option>
            <option value="erro">Com erro</option>
          </select>

          <select
            value={filtroAlgoritmo}
            onChange={(evento) => setFiltroAlgoritmo(evento.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 outline-none focus:border-emerald-500"
          >
            <option value="todos">Todos os algoritmos</option>
            <option value="zscore">Z-Score</option>
            <option value="iqr">IQR</option>
            <option value="isolation_forest">Isolation Forest</option>
            <option value="lof">LOF</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="rounded-3xl border border-slate-200 bg-white p-20 shadow-sm flex flex-col items-center justify-center gap-4">
          <Loader2 className="w-10 h-10 animate-spin text-emerald-500" />
          <p className="text-slate-500 font-medium">Carregando historico de analises...</p>
        </div>
      ) : analisesFiltradas.length > 0 ? (
        <div className="space-y-5">
          {analisesFiltradas.map((analise) => (
            <article key={analise.id} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div className="space-y-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="rounded-lg bg-slate-100 px-2 py-1 text-xs font-bold uppercase text-slate-600">
                      {formatarAlgoritmo(analise.algoritmo)}
                    </span>
                    <span className="rounded-lg bg-blue-50 px-2 py-1 text-xs font-bold uppercase text-blue-700 border border-blue-100">
                      {analise.tipo_algoritmo}
                    </span>
                    <span className={`rounded-lg px-2 py-1 text-xs font-bold uppercase ${obterEstiloStatus(analise.status)}`}>
                      {analise.status}
                    </span>
                  </div>

                  <div>
                    <h2 className="text-xl font-bold text-slate-900">{analise.nome}</h2>
                    <p className="mt-1 text-sm text-slate-500">
                      Dataset #{analise.dataset_id} | {new Date(analise.criado_em).toLocaleString('pt-BR')}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 flex-wrap">
                  <Link
                    to={`/analise/resultado/${analise.id}`}
                    className="inline-flex items-center gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700 transition-colors hover:bg-emerald-100"
                  >
                    Ver resultado
                    <ArrowRight className="w-4 h-4" />
                  </Link>

                  <button
                    type="button"
                    onClick={() => baixarResultado(analise)}
                    disabled={analise.status !== 'concluido' || analiseBaixandoId === analise.id}
                    className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {analiseBaixandoId === analise.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Download className="w-4 h-4" />
                    )}
                    Exportar CSV
                  </button>
                </div>
              </div>

              <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                  <p className="text-[10px] font-bold uppercase text-slate-400">Colunas analisadas</p>
                  <p className="mt-2 text-lg font-bold text-slate-900">{analise.colunas_selecionadas.length}</p>
                </div>
                <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                  <p className="text-[10px] font-bold uppercase text-slate-400">Anomalias</p>
                  <p className="mt-2 text-lg font-bold text-red-600">{analise.resultado_resumo?.total_anomalias ?? 0}</p>
                </div>
                <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                  <p className="text-[10px] font-bold uppercase text-slate-400">Score maximo</p>
                  <p className="mt-2 text-lg font-bold text-slate-900">
                    {(analise.resultado_resumo?.score_maximo ?? 0).toFixed(4)}
                  </p>
                </div>
                <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                  <p className="text-[10px] font-bold uppercase text-slate-400">Percentual anomalo</p>
                  <p className="mt-2 text-lg font-bold text-slate-900">
                    {(analise.resultado_resumo?.percentual_anomalias ?? 0).toFixed(2)}%
                  </p>
                </div>
              </div>

              {analise.status === 'erro' ? (
                <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
                  <span>{analise.resultado_resumo?.erro || 'A analise foi finalizada com erro interno.'}</span>
                </div>
              ) : (
                <div className="mt-6 rounded-2xl border border-slate-100 bg-slate-50 p-4">
                  <div className="flex items-start gap-3">
                    {analise.status === 'concluido' ? (
                      <CheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                    ) : (
                      <Clock className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                    )}
                    <p className="text-sm text-slate-700">
                      {analise.resultado_resumo?.interpretacao_geral ||
                        (analise.status === 'processando'
                          ? 'A analise ainda esta em processamento. Abra o resultado para acompanhar a atualizacao automatica.'
                          : 'Nao ha interpretacao detalhada disponivel para esta execucao.')}
                    </p>
                  </div>
                </div>
              )}
            </article>
          ))}
        </div>
      ) : semResultadosComFiltro ? (
        <div className="rounded-3xl border border-slate-200 bg-white p-20 shadow-sm text-center">
          <Search className="mx-auto h-10 w-10 text-slate-300" />
          <h2 className="mt-4 text-lg font-bold text-slate-900">Nenhuma analise corresponde aos filtros</h2>
          <p className="mt-1 text-sm text-slate-500">Ajuste a busca ou os filtros para encontrar uma execucao anterior.</p>
        </div>
      ) : (
        <div className="rounded-3xl border border-slate-200 bg-white p-20 shadow-sm text-center">
          <Activity className="mx-auto h-10 w-10 text-slate-300" />
          <h2 className="mt-4 text-lg font-bold text-slate-900">Nenhuma analise registrada</h2>
          <p className="mt-1 text-sm text-slate-500">Crie sua primeira analise para acompanhar os resultados por aqui.</p>
          <Link
            to="/analise/nova"
            className="mt-6 inline-flex items-center gap-2 rounded-2xl bg-emerald-500 px-5 py-3 text-sm font-bold text-white transition-colors hover:bg-emerald-600"
          >
            <Activity className="w-4 h-4" />
            Nova Analise
          </Link>
        </div>
      )}

      <ModalConfirmacaoExclusaoHistorico
        aberto={modalExclusaoAberto}
        carregando={exclusaoHistoricoMutation.isPending}
        quantidadeAnalises={totalAnalises}
        erro={erroAcao}
        onConfirmar={() => exclusaoHistoricoMutation.mutate()}
        onFechar={() => {
          if (exclusaoHistoricoMutation.isPending) {
            return;
          }
          setErroAcao(null);
          setModalExclusaoAberto(false);
        }}
      />
    </div>
  );
};

export default HistoricoAnalises;
