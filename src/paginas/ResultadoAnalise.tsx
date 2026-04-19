/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  BookOpen,
  CheckCircle,
  Download,
  ExternalLink,
  FileSearch,
  FileText,
  Loader2,
  MapPin,
  ShieldAlert,
} from 'lucide-react';
import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
} from 'recharts';
import { analiseServico } from '../servicos/analiseServico';
import { extrairMensagemErroApi } from '../servicos/api';
import { Analise, AnomaliaDetalhada, ColunaRelevanteAnomalia, TipoAnomaliaEncontrada } from '../tipos';

const CORES_GRAFICO = ['#10b981', '#ef4444'];

/**
 * Retorna os parametros efetivos que devem ser exibidos ao usuario.
 */
function obterParametrosEfetivos(analise: Analise): Record<string, number> {
  const parametrosResumo = analise.resultado_resumo?.parametros_utilizados;
  const parametrosAtuais = (parametrosResumo || analise.parametros || {}) as Record<string, number>;

  if (analise.algoritmo === 'zscore') {
    return { threshold: Number(parametrosAtuais.threshold ?? 3) };
  }

  if (analise.algoritmo === 'iqr') {
    return { fator: Number(parametrosAtuais.fator ?? 1.5) };
  }

  if (analise.algoritmo === 'isolation_forest') {
    return {
      contaminacao: Number(parametrosAtuais.contaminacao ?? 0.05),
      n_estimadores: Number(parametrosAtuais.n_estimadores ?? 100),
    };
  }

  if (analise.algoritmo === 'lof') {
    return {
      contaminacao: Number(parametrosAtuais.contaminacao ?? 0.05),
      n_vizinhos: Number(parametrosAtuais.n_vizinhos ?? 20),
    };
  }

  return {};
}

/**
 * Gera um texto claro explicando como ler o resultado do algoritmo executado.
 */
function obterExplicacaoResultado(analise: Analise): string {
  const interpretacaoBackend = analise.resultado_resumo?.interpretacao_geral;
  if (interpretacaoBackend) {
    return interpretacaoBackend;
  }

  const parametros = obterParametrosEfetivos(analise);
  const resumo = analise.resultado_resumo;
  const totalAnomalias = resumo?.total_anomalias ?? 0;
  const percentualAnomalias = resumo?.percentual_anomalias ?? 0;
  const scoreMaximo = resumo?.score_maximo ?? 0;

  if (analise.algoritmo === 'zscore') {
    const threshold = parametros.threshold ?? 3;
    if (totalAnomalias === 0) {
      return `Nenhum registro ultrapassou o limiar de ${threshold.toFixed(2)} desvios padrao. O maior Z-Score observado foi ${scoreMaximo.toFixed(2)}.`;
    }

    return `${totalAnomalias} registro(s) ultrapassaram o limiar de ${threshold.toFixed(2)} desvios padrao, representando ${percentualAnomalias.toFixed(2)}% do dataset.`;
  }

  if (analise.algoritmo === 'iqr') {
    const fator = parametros.fator ?? 1.5;
    if (totalAnomalias === 0) {
      return `Nenhum registro ficou fora dos limites definidos por Q1 - ${fator.toFixed(2)}*IQR e Q3 + ${fator.toFixed(2)}*IQR.`;
    }

    return `${totalAnomalias} registro(s) ficaram fora dos limites interquartis calculados com fator ${fator.toFixed(2)}.`;
  }

  if (analise.algoritmo === 'isolation_forest') {
    const contaminacao = (parametros.contaminacao ?? 0.05) * 100;
    return `O Isolation Forest isolou ${totalAnomalias} registro(s) como suspeitos. A configuracao usa contaminacao estimada de ${contaminacao.toFixed(2)}%.`;
  }

  if (analise.algoritmo === 'lof') {
    const nVizinhos = parametros.n_vizinhos ?? 20;
    return `O LOF marcou ${totalAnomalias} registro(s) por apresentarem densidade local atipica em comparacao com ${nVizinhos} vizinhos.`;
  }

  return `${totalAnomalias} registro(s) foram sinalizados para revisao manual.`;
}

/**
 * Retorna um resumo operacional curto para a faixa principal da tela.
 */
function obterResumoExecutivo(analise: Analise): { titulo: string; descricao: string; destaque: 'sucesso' | 'alerta' } {
  const resumo = analise.resultado_resumo;
  const totalAnomalias = resumo?.total_anomalias ?? 0;

  if (totalAnomalias === 0) {
    return {
      titulo: 'Nenhuma anomalia critica identificada',
      descricao: obterExplicacaoResultado(analise),
      destaque: 'sucesso',
    };
  }

  return {
    titulo: 'Analise concluida com registros suspeitos',
    descricao: obterExplicacaoResultado(analise),
    destaque: 'alerta',
  };
}

/**
 * Formata valores para exibicao curta na interface.
 */
function formatarValor(valor: unknown): string {
  if (valor === null || valor === undefined || valor === '') {
    return '-';
  }

  if (typeof valor === 'number') {
    return Number.isInteger(valor) ? valor.toLocaleString('pt-BR') : valor.toLocaleString('pt-BR', { maximumFractionDigits: 4 });
  }

  return String(valor);
}

/**
 * Renderiza o bloco das colunas que mais explicam a anomalia.
 */
function BlocoColunasRelevantes({ colunasRelevantes }: { colunasRelevantes: ColunaRelevanteAnomalia[] }) {
  return (
    <div className="space-y-3">
      {colunasRelevantes.map((coluna) => (
        <div key={`${coluna.coluna}-${coluna.score_coluna ?? 'sem-score'}`} className="p-4 bg-slate-50 rounded-2xl border border-slate-200">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-bold text-slate-900">{coluna.coluna}</p>
            {coluna.score_coluna !== undefined && coluna.score_coluna !== null && (
              <span className="text-xs font-bold px-2 py-1 rounded-lg bg-slate-900 text-white">
                Score {formatarValor(coluna.score_coluna)}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-2">{coluna.motivo}</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-xs">
            <div>
              <p className="text-slate-400 uppercase font-bold">Valor original</p>
              <p className="text-slate-700 mt-1">{formatarValor(coluna.valor_original)}</p>
            </div>
            {coluna.valor_analisado !== undefined && (
              <div>
                <p className="text-slate-400 uppercase font-bold">Valor analisado</p>
                <p className="text-slate-700 mt-1">{formatarValor(coluna.valor_analisado)}</p>
              </div>
            )}
            {coluna.media_referencia !== undefined && (
              <div>
                <p className="text-slate-400 uppercase font-bold">Media ref.</p>
                <p className="text-slate-700 mt-1">{formatarValor(coluna.media_referencia)}</p>
              </div>
            )}
            {coluna.mediana_referencia !== undefined && (
              <div>
                <p className="text-slate-400 uppercase font-bold">Mediana ref.</p>
                <p className="text-slate-700 mt-1">{formatarValor(coluna.mediana_referencia)}</p>
              </div>
            )}
            {coluna.limite_inferior !== undefined && (
              <div>
                <p className="text-slate-400 uppercase font-bold">Limite inf.</p>
                <p className="text-slate-700 mt-1">{formatarValor(coluna.limite_inferior)}</p>
              </div>
            )}
            {coluna.limite_superior !== undefined && (
              <div>
                <p className="text-slate-400 uppercase font-bold">Limite sup.</p>
                <p className="text-slate-700 mt-1">{formatarValor(coluna.limite_superior)}</p>
              </div>
            )}
            {coluna.q1_referencia !== undefined && (
              <div>
                <p className="text-slate-400 uppercase font-bold">Q1</p>
                <p className="text-slate-700 mt-1">{formatarValor(coluna.q1_referencia)}</p>
              </div>
            )}
            {coluna.q3_referencia !== undefined && (
              <div>
                <p className="text-slate-400 uppercase font-bold">Q3</p>
                <p className="text-slate-700 mt-1">{formatarValor(coluna.q3_referencia)}</p>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Renderiza uma lista detalhada dos registros marcados como anomalia.
 */
function ListaAnomalias({ anomalias }: { anomalias: AnomaliaDetalhada[] }) {
  if (anomalias.length === 0) {
    return (
      <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-2xl text-sm text-emerald-800">
        Nenhuma anomalia detalhada foi registrada para esta execucao.
      </div>
    );
  }

  return (
    <div className="max-h-[42rem] overflow-y-auto pr-2 space-y-4">
      {anomalias.map((anomalia) => (
        <article key={`${anomalia.tipo_principal}-${anomalia.indice_original}-${anomalia.score}`} className="p-6 bg-white rounded-3xl border border-slate-200 shadow-sm">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-bold px-2 py-1 rounded-lg bg-red-100 text-red-700 uppercase">{anomalia.tipo_principal_nome}</span>
                <span className="text-xs font-bold px-2 py-1 rounded-lg bg-slate-100 text-slate-700">Score {formatarValor(anomalia.score)}</span>
              </div>
              <div className="flex items-center gap-2 mt-3 text-sm text-slate-500">
                <MapPin className="w-4 h-4" />
                <span>{anomalia.localizacao}</span>
              </div>
            </div>
          </div>

          <p className="text-sm text-slate-700 mt-4">{anomalia.justificativa}</p>

          <div className="mt-5">
            <h5 className="text-sm font-bold text-slate-900 mb-3">Onde o comportamento ficou fora do padrao</h5>
            <BlocoColunasRelevantes colunasRelevantes={anomalia.colunas_relevantes} />
          </div>

          <div className="mt-5">
            <h5 className="text-sm font-bold text-slate-900 mb-3">Valores do registro analisado</h5>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(anomalia.dados_registro).map(([chave, valor]) => (
                <div key={chave} className="p-3 bg-slate-50 rounded-2xl border border-slate-200">
                  <p className="text-[10px] uppercase font-bold text-slate-400">{chave}</p>
                  <p className="text-sm text-slate-700 mt-1 break-words">{formatarValor(valor)}</p>
                </div>
              ))}
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

/**
 * Renderiza o dicionario dos tipos de anomalia encontrados nesta execucao.
 */
function DicionarioTipos({ tipos }: { tipos: TipoAnomaliaEncontrada[] }) {
  if (tipos.length === 0) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {tipos.map((tipo) => (
        <div key={tipo.codigo} className="p-5 bg-white rounded-3xl border border-slate-200 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div>
              <span className="inline-flex text-[10px] font-bold px-2 py-1 rounded-lg bg-slate-100 text-slate-600 uppercase tracking-wide">
                {tipo.codigo}
              </span>
              <p className="text-sm font-bold text-slate-900">{tipo.nome}</p>
              <p className="text-xs text-slate-500 mt-1">{tipo.descricao}</p>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold text-emerald-600">{tipo.quantidade}</p>
              <p className="text-xs text-slate-400">{tipo.percentual.toFixed(2)}%</p>
            </div>
          </div>
          <div className="mt-4 p-3 bg-slate-50 rounded-2xl border border-slate-100">
            <p className="text-[10px] uppercase font-bold text-slate-400">Criterio</p>
            <p className="text-xs text-slate-600 mt-1">{tipo.criterio}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

const ResultadoAnalise: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [baixandoArquivo, setBaixandoArquivo] = useState(false);
  const [erroDownload, setErroDownload] = useState<string | null>(null);

  const { data: analise, isLoading, error } = useQuery({
    queryKey: ['analise', id],
    queryFn: () => analiseServico.obterPorId(parseInt(id!, 10)),
    enabled: !!id,
    refetchInterval: (query) => (query.state.data?.status === 'processando' ? 3000 : false),
  });

  /**
   * Baixa o CSV gerado pela analise usando a mesma autenticacao do frontend.
   */
  const handleDownload = async () => {
    if (!analise) {
      return;
    }

    setBaixandoArquivo(true);
    setErroDownload(null);

    try {
      await analiseServico.baixarResultado(analise.id);
    } catch (erroApi) {
      setErroDownload(extrairMensagemErroApi(erroApi, 'Nao foi possivel baixar o arquivo da analise.'));
    } finally {
      setBaixandoArquivo(false);
    }
  };

  if (isLoading) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center gap-4">
        <Loader2 className="w-12 h-12 text-emerald-500 animate-spin" />
        <div className="text-center">
          <h2 className="text-xl font-bold text-slate-900">Processando analise...</h2>
          <p className="text-slate-500 text-sm mt-1">Estamos aplicando os algoritmos de deteccao em seus dados.</p>
        </div>
      </div>
    );
  }

  if (error || !analise) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center gap-4 text-center">
        <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center">
          <AlertCircle className="w-8 h-8" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900">Erro ao carregar analise</h2>
          <p className="text-slate-500 text-sm mt-1">Nao foi possivel recuperar os resultados desta analise.</p>
        </div>
        <Link to="/historico" className="text-emerald-600 font-bold hover:underline flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Voltar para o historico
        </Link>
      </div>
    );
  }

  const resumo = analise.resultado_resumo;
  const parametros = obterParametrosEfetivos(analise);
  const tiposEncontrados = resumo?.tipos_anomalia_encontrados ?? [];
  const anomaliasDetalhadas = resumo?.anomalias_detalhadas ?? [];
  const resumoExecutivo = obterResumoExecutivo(analise);
  const dadosGrafico = [
    { name: 'Normais', value: Math.max((resumo?.total_registros || 0) - (resumo?.total_anomalias || 0), 0) },
    { name: 'Anomalias', value: resumo?.total_anomalias || 0 },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link to="/historico" className="p-2 hover:bg-slate-100 rounded-xl transition-colors text-slate-400">
            <ArrowLeft className="w-6 h-6" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">{analise.nome}</h1>
            <div className="flex items-center gap-3 mt-1 flex-wrap">
              <span className="text-xs font-bold px-2 py-0.5 bg-slate-100 text-slate-600 rounded-md uppercase">{analise.algoritmo}</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-md uppercase">{analise.status}</span>
              <p className="text-slate-500 text-sm">Executada em {new Date(analise.criado_em).toLocaleString()}</p>
            </div>
          </div>
        </div>

        {analise.status === 'concluido' && (
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleDownload}
              disabled={baixandoArquivo}
              className="bg-slate-900 hover:bg-slate-800 text-white font-bold py-3 px-6 rounded-2xl shadow-lg transition-all flex items-center gap-2 disabled:opacity-60"
            >
              {baixandoArquivo ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />}
              Exportar CSV
            </button>
            
            <Link
              to={`/analise/${analise.id}/dados-tratados`}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-6 rounded-2xl shadow-lg transition-all flex items-center gap-2"
            >
              <Database className="w-5 h-5" /> Ver Dados Tratados
            </Link>
            
            <Link
              to={`/analise/${analise.id}/relatorios`}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-2xl shadow-lg transition-all flex items-center gap-2"
            >
              <FileText className="w-5 h-5" /> Gerar Relatorio PDF/HTML
            </Link>
          </div>
        )}
      </div>

      {erroDownload && (
        <div className="bg-red-50 border border-red-200 p-4 rounded-2xl text-red-700 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{erroDownload}</span>
        </div>
      )}

      {analise.status === 'processando' ? (
        <div className="bg-amber-50 border border-amber-200 p-8 rounded-3xl flex items-center gap-6">
          <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-2xl flex items-center justify-center animate-pulse">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-amber-900">Analise em andamento</h3>
            <p className="text-amber-700 text-sm">O sistema esta processando os dados. Esta pagina sera atualizada automaticamente.</p>
          </div>
        </div>
      ) : analise.status === 'erro' ? (
        <div className="bg-red-50 border border-red-200 p-8 rounded-3xl flex items-center gap-6">
          <div className="w-12 h-12 bg-red-100 text-red-600 rounded-2xl flex items-center justify-center">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-red-900">Falha na execucao</h3>
            <p className="text-red-700 text-sm">{resumo?.erro || 'Ocorreu um erro desconhecido durante o processamento.'}</p>
          </div>
        </div>
      ) : (
        <>
          <div
            className={`p-6 rounded-3xl border flex items-start gap-4 ${
              resumoExecutivo.destaque === 'sucesso'
                ? 'bg-emerald-50 border-emerald-200'
                : 'bg-amber-50 border-amber-200'
            }`}
          >
            <div
              className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${
                resumoExecutivo.destaque === 'sucesso'
                  ? 'bg-emerald-100 text-emerald-600'
                  : 'bg-amber-100 text-amber-600'
              }`}
            >
              {resumoExecutivo.destaque === 'sucesso' ? <CheckCircle className="w-6 h-6" /> : <ShieldAlert className="w-6 h-6" />}
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">{resumoExecutivo.titulo}</h2>
              <p className="text-sm text-slate-600 mt-1">{resumoExecutivo.descricao}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Total analisado</p>
              <h3 className="text-2xl font-bold text-slate-900">{resumo?.total_registros?.toLocaleString() ?? 0}</h3>
              <p className="text-xs text-slate-500 mt-1">Registros avaliados no dataset</p>
            </div>
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Anomalias</p>
              <h3 className="text-2xl font-bold text-red-600">{resumo?.total_anomalias?.toLocaleString() ?? 0}</h3>
              <p className="text-xs text-slate-500 mt-1">{(resumo?.percentual_anomalias ?? 0).toFixed(2)}% do total</p>
            </div>
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Score medio</p>
              <h3 className="text-2xl font-bold text-blue-600">{(resumo?.score_medio ?? 0).toFixed(4)}</h3>
              <p className="text-xs text-slate-500 mt-1">Media da pontuacao de anomalia</p>
            </div>
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Score maximo</p>
              <h3 className="text-2xl font-bold text-amber-600">{(resumo?.score_maximo ?? 0).toFixed(4)}</h3>
              <p className="text-xs text-slate-500 mt-1">Maior desvio observado</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-200">
              <h3 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-emerald-500" /> Distribuicao dos registros
              </h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={dadosGrafico}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {dadosGrafico.map((entrada, indice) => (
                        <Cell key={`celula-${indice}`} fill={CORES_GRAFICO[indice % CORES_GRAFICO.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip
                      contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    />
                    <Legend verticalAlign="bottom" height={36} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-6 p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <p className="text-xs text-slate-600 leading-relaxed">{obterExplicacaoResultado(analise)}</p>
              </div>
            </div>

            <div className="lg:col-span-2 bg-white p-8 rounded-3xl shadow-sm border border-slate-200">
              <h3 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-500" /> Relatorio tecnico da execucao
              </h3>

              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-slate-400 uppercase">Algoritmo utilizado</p>
                    <p className="text-sm text-slate-700 font-medium">{analise.algoritmo.toUpperCase()} ({analise.tipo_algoritmo})</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-slate-400 uppercase">Colunas analisadas</p>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {analise.colunas_selecionadas.map((coluna) => (
                        <span key={coluna} className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md font-bold">
                          {coluna}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Object.entries(parametros).map(([chave, valor]) => (
                    <div key={chave} className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                      <p className="text-xs font-bold text-slate-400 uppercase">{chave}</p>
                      <p className="text-lg font-bold text-slate-900 mt-1">{Number(valor).toLocaleString('pt-BR')}</p>
                    </div>
                  ))}
                </div>

                <div className="space-y-4">
                  <div className="flex gap-4 p-4 bg-emerald-50 rounded-2xl border border-emerald-100">
                    <CheckCircle className="w-5 h-5 text-emerald-500 shrink-0" />
                    <p className="text-sm text-emerald-800">
                      O processamento foi concluido com sucesso. Foram identificados <span className="font-bold">{resumo?.total_anomalias ?? 0}</span> registro(s) fora do comportamento esperado.
                    </p>
                  </div>
                  <div className="flex gap-4 p-4 bg-blue-50 rounded-2xl border border-blue-100">
                    <ExternalLink className="w-5 h-5 text-blue-500 shrink-0" />
                    <p className="text-sm text-blue-800">
                      O arquivo exportado inclui as colunas <code className="bg-white px-1 rounded">anomalia_flag</code> e <code className="bg-white px-1 rounded">anomalia_score</code> para facilitar auditoria externa.
                    </p>
                  </div>
                  <div className="flex gap-4 p-4 bg-slate-50 rounded-2xl border border-slate-200">
                    <BarChart3 className="w-5 h-5 text-slate-500 shrink-0" />
                    <p className="text-sm text-slate-700">{obterExplicacaoResultado(analise)}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <section className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center">
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900">Dicionario dos tipos de anomalia encontrados</h3>
                <p className="text-sm text-slate-500">Resumo semantico das categorias identificadas nesta execucao.</p>
              </div>
            </div>
            <DicionarioTipos tipos={tiposEncontrados} />
          </section>

          <section className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center">
                <FileSearch className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900">Onde e por que cada registro foi marcado</h3>
                <p className="text-sm text-slate-500">
                  Cada card abaixo explica a localizacao da anomalia, o motivo do alerta e as colunas que mais contribuiram para o resultado.
                </p>
              </div>
            </div>
            <ListaAnomalias anomalias={anomaliasDetalhadas} />
          </section>

          <div className="pt-2">
            <h4 className="text-sm font-bold text-slate-900 mb-3">Proximos passos sugeridos</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link to="/analise/nova" className="p-4 border border-slate-200 rounded-2xl hover:border-emerald-500 hover:bg-emerald-50 transition-all group">
                <p className="text-sm font-bold text-slate-900 group-hover:text-emerald-700">Nova analise</p>
                <p className="text-xs text-slate-500 mt-1">Compare este resultado com outro algoritmo para ganhar confianca.</p>
              </Link>
              <Link to="/datasets" className="p-4 border border-slate-200 rounded-2xl hover:border-blue-500 hover:bg-blue-50 transition-all group">
                <p className="text-sm font-bold text-slate-900 group-hover:text-blue-700">Voltar aos datasets</p>
                <p className="text-xs text-slate-500 mt-1">Revise o dataset original e refine as colunas analisadas.</p>
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ResultadoAnalise;
