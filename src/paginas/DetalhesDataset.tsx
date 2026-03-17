/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  Database,
  FileSpreadsheet,
  FileText,
  HardDrive,
  Loader2,
  Trash2,
} from 'lucide-react';
import ModalConfirmacaoExclusaoDataset from '../componentes/datasets/ModalConfirmacaoExclusaoDataset';
import { extrairMensagemErroApi } from '../servicos/api';
import { datasetServico } from '../servicos/datasetServico';
import { Dataset, MetadadosColuna } from '../tipos';

const DetalhesDataset: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [erroAcao, setErroAcao] = useState<string | null>(null);
  const [modalExclusaoAberto, setModalExclusaoAberto] = useState(false);
  const datasetId = Number(id);

  const { data: dataset, isLoading, error } = useQuery({
    queryKey: ['dataset', datasetId],
    queryFn: () => datasetServico.obterPorId(datasetId),
    enabled: Number.isFinite(datasetId),
    initialData: () =>
      queryClient.getQueryData<Dataset[]>(['datasets'])?.find((datasetAtual) => datasetAtual.id === datasetId),
  });

  /**
   * Exclui o dataset atual e redireciona o usuario de volta para a listagem.
   */
  const exclusaoMutation = useMutation({
    mutationFn: (idAtual: number) => datasetServico.excluir(idAtual),
    onSuccess: (resultado, idExcluido) => {
      queryClient.setQueryData<Dataset[]>(['datasets'], (datasetsAtuais) =>
        (datasetsAtuais ?? []).filter((datasetAtual) => datasetAtual.id !== idExcluido)
      );
      queryClient.removeQueries({ queryKey: ['dataset', idExcluido] });
      void queryClient.invalidateQueries({ queryKey: ['datasets'] });
      navigate('/datasets', {
        replace: true,
        state: {
          mensagemSucesso:
            resultado.analises_removidas > 0
              ? `${resultado.mensagem} ${resultado.analises_removidas} analise(s) relacionada(s) tambem foram removidas.`
              : resultado.mensagem,
        },
      });
    },
    onError: (erroApi) => {
      setErroAcao(extrairMensagemErroApi(erroApi, 'Nao foi possivel excluir o dataset.'));
    },
  });

  /**
   * Formata o tamanho do arquivo em bytes, KB ou MB.
   */
  const formatarTamanho = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  /**
   * Formata numeros curtos das estatisticas das colunas para exibicao amigavel.
   */
  const formatarNumero = (valor?: number) => {
    if (valor === undefined || valor === null || Number.isNaN(valor)) {
      return '-';
    }

    return Number.isInteger(valor)
      ? valor.toLocaleString('pt-BR')
      : valor.toLocaleString('pt-BR', { maximumFractionDigits: 4 });
  };

  /**
   * Renderiza um conjunto compacto de estatisticas da coluna selecionada.
   */
  const renderizarEstatisticasColuna = (coluna: MetadadosColuna) => {
    const estatisticas = Object.entries(coluna.estatisticas ?? {});

    if (estatisticas.length === 0) {
      return <p className="text-xs text-slate-400">Sem estatisticas numericas disponiveis.</p>;
    }

    return (
      <div className="grid grid-cols-2 gap-3 mt-3">
        {estatisticas.map(([chave, valor]) => (
          <div key={chave} className="rounded-2xl border border-slate-100 bg-slate-50 p-3">
            <p className="text-[10px] font-bold uppercase text-slate-400">{chave}</p>
            <p className="mt-1 text-sm text-slate-700">{formatarNumero(valor as number)}</p>
          </div>
        ))}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center gap-4">
        <Loader2 className="w-12 h-12 text-emerald-500 animate-spin" />
        <div className="text-center">
          <h2 className="text-xl font-bold text-slate-900">Carregando dataset...</h2>
          <p className="text-slate-500 text-sm mt-1">Estamos buscando os metadados detalhados do arquivo enviado.</p>
        </div>
      </div>
    );
  }

  if (error || !dataset) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center gap-4 text-center">
        <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center">
          <AlertCircle className="w-8 h-8" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900">Dataset nao encontrado</h2>
          <p className="text-slate-500 text-sm mt-1">Nao foi possivel carregar os detalhes deste dataset.</p>
        </div>
        <Link to="/datasets" className="text-emerald-600 font-bold hover:underline flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Voltar para Meus Datasets
        </Link>
      </div>
    );
  }

  const totalLinhas = dataset.metadados?.total_linhas ?? 0;
  const totalColunas = dataset.metadados?.colunas?.length ?? 0;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-start gap-4">
          <Link to="/datasets" className="mt-1 rounded-xl p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600">
            <ArrowLeft className="h-6 w-6" />
          </Link>
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-3xl font-bold text-slate-900 tracking-tight">{dataset.nome}</h1>
              <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-bold uppercase text-slate-600">
                {dataset.formato}
              </span>
            </div>
            <p className="mt-2 max-w-3xl text-sm text-slate-500">
              {dataset.descricao || 'Nenhuma descricao foi informada para este dataset.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <Link
            to="/analise/nova"
            className="rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-3 text-sm font-bold text-emerald-700 transition-colors hover:bg-emerald-100"
          >
            Nova analise
          </Link>
          <button
            type="button"
            onClick={() => {
              setErroAcao(null);
              setModalExclusaoAberto(true);
            }}
            className="rounded-2xl bg-red-600 px-5 py-3 text-sm font-bold text-white transition-colors hover:bg-red-700"
            data-excluir-dataset
          >
            <span className="inline-flex items-center gap-2">
              <Trash2 className="h-4 w-4" />
              Excluir dataset
            </span>
          </button>
        </div>
      </div>

      {dataset.metadados?.aviso_importacao && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{dataset.metadados.aviso_importacao}</span>
        </div>
      )}

      {erroAcao && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{erroAcao}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Formato</p>
          <div className="mt-4 flex items-center gap-3">
            {dataset.formato === 'csv' ? <FileText className="h-5 w-5 text-emerald-500" /> : <FileSpreadsheet className="h-5 w-5 text-emerald-500" />}
            <p className="text-lg font-bold text-slate-900">{dataset.formato.toUpperCase()}</p>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Linhas importadas</p>
          <div className="mt-4 flex items-center gap-3">
            <Database className="h-5 w-5 text-blue-500" />
            <p className="text-lg font-bold text-slate-900">{totalLinhas.toLocaleString('pt-BR')}</p>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Colunas detectadas</p>
          <div className="mt-4 flex items-center gap-3">
            <Database className="h-5 w-5 text-violet-500" />
            <p className="text-lg font-bold text-slate-900">{totalColunas.toLocaleString('pt-BR')}</p>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Tamanho</p>
          <div className="mt-4 flex items-center gap-3">
            <HardDrive className="h-5 w-5 text-amber-500" />
            <p className="text-lg font-bold text-slate-900">{formatarTamanho(dataset.tamanho_bytes)}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <section className="xl:col-span-1 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900">Informacoes do arquivo</h2>
          <div className="mt-6 space-y-5">
            <div>
              <p className="text-xs font-bold uppercase text-slate-400">Data de upload</p>
              <p className="mt-2 flex items-center gap-2 text-sm text-slate-700">
                <Calendar className="h-4 w-4 text-slate-400" />
                {new Date(dataset.criado_em).toLocaleString('pt-BR')}
              </p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-400">Codificacao</p>
              <p className="mt-2 text-sm text-slate-700">{dataset.metadados?.codificacao || 'Nao se aplica'}</p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-400">Separador</p>
              <p className="mt-2 text-sm text-slate-700">{dataset.metadados?.separador || 'Nao se aplica'}</p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-400">Linhas descartadas</p>
              <p className="mt-2 text-sm text-slate-700">{dataset.metadados?.linhas_descartadas ?? 0}</p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase text-slate-400">Linhas com problema</p>
              <p className="mt-2 text-sm text-slate-700">
                {(dataset.metadados?.linhas_com_problema ?? []).length > 0
                  ? dataset.metadados?.linhas_com_problema?.join(', ')
                  : 'Nenhuma'}
              </p>
            </div>
          </div>
        </section>

        <section className="xl:col-span-2 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Colunas e metadados</h2>
              <p className="mt-1 text-sm text-slate-500">
                Revise os tipos detectados e as estatisticas basicas antes de criar novas analises.
              </p>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            {(dataset.metadados?.colunas ?? []).map((coluna) => (
              <article key={coluna.nome} className="rounded-3xl border border-slate-200 bg-slate-50/60 p-5">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">{coluna.nome}</h3>
                    <p className="mt-1 text-xs text-slate-500">Tipo detectado: {coluna.tipo}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-right">
                    <p className="text-[10px] font-bold uppercase text-slate-400">Nulos</p>
                    <p className="mt-1 text-sm font-bold text-slate-900">
                      {coluna.valores_nulos} ({coluna.percentual_nulos.toFixed(2)}%)
                    </p>
                  </div>
                </div>
                {renderizarEstatisticasColuna(coluna)}
              </article>
            ))}
          </div>
        </section>
      </div>

      <ModalConfirmacaoExclusaoDataset
        nomeDataset={dataset.nome}
        aberto={modalExclusaoAberto}
        carregando={exclusaoMutation.isPending}
        erro={erroAcao}
        onConfirmar={() => exclusaoMutation.mutate(dataset.id)}
        onFechar={() => {
          if (exclusaoMutation.isPending) {
            return;
          }
          setErroAcao(null);
          setModalExclusaoAberto(false);
        }}
      />
    </div>
  );
};

export default DetalhesDataset;
