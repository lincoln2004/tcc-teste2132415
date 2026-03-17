/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Calendar,
  Database,
  FileSpreadsheet,
  FileText,
  HardDrive,
  MoreVertical,
  Plus,
  Search,
  Trash2,
} from 'lucide-react';
import ModalConfirmacaoExclusaoDataset from '../componentes/datasets/ModalConfirmacaoExclusaoDataset';
import { extrairMensagemErroApi } from '../servicos/api';
import { datasetServico } from '../servicos/datasetServico';
import { Dataset } from '../tipos';

const ListagemDatasets: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [termoBusca, setTermoBusca] = useState('');
  const [menuAbertoId, setMenuAbertoId] = useState<number | null>(null);
  const [datasetParaExcluir, setDatasetParaExcluir] = useState<Dataset | null>(null);
  const [mensagemAcao, setMensagemAcao] = useState<string | null>(null);
  const [erroAcao, setErroAcao] = useState<string | null>(null);

  const { data: datasets, isLoading, error } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetServico.listar,
  });

  useEffect(() => {
    const mensagemSucesso = (location.state as { mensagemSucesso?: string } | null)?.mensagemSucesso;
    if (!mensagemSucesso) {
      return;
    }

    setMensagemAcao(mensagemSucesso);
    navigate(location.pathname, { replace: true, state: null });
  }, [location.pathname, location.state, navigate]);

  /**
   * Exclui o dataset selecionado e sincroniza imediatamente o cache local da listagem.
   */
  const exclusaoMutation = useMutation({
    mutationFn: (datasetId: number) => datasetServico.excluir(datasetId),
    onSuccess: (resultado, datasetId) => {
      queryClient.setQueryData<Dataset[]>(['datasets'], (datasetsAtuais) =>
        (datasetsAtuais ?? []).filter((dataset) => dataset.id !== datasetId)
      );
      queryClient.removeQueries({ queryKey: ['dataset', datasetId] });
      void queryClient.invalidateQueries({ queryKey: ['datasets'] });

      setErroAcao(null);
      setMenuAbertoId(null);
      setDatasetParaExcluir(null);
      setMensagemAcao(
        resultado.analises_removidas > 0
          ? `${resultado.mensagem} ${resultado.analises_removidas} analise(s) relacionada(s) tambem foram removidas.`
          : resultado.mensagem
      );
    },
    onError: (erroApi) => {
      setMensagemAcao(null);
      setErroAcao(extrairMensagemErroApi(erroApi, 'Nao foi possivel excluir o dataset.'));
    },
  });

  /**
   * Formata o tamanho do arquivo em unidades legiveis para a tabela.
   */
  const formatarTamanho = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  /**
   * Aplica o filtro digitado considerando nome, descricao e formato do dataset.
   */
  const datasetsFiltrados = useMemo(() => {
    const termoNormalizado = termoBusca.trim().toLowerCase();
    if (!termoNormalizado) {
      return datasets ?? [];
    }

    return (datasets ?? []).filter((dataset) =>
      [dataset.nome, dataset.descricao ?? '', dataset.formato]
        .some((valor) => valor.toLowerCase().includes(termoNormalizado))
    );
  }, [datasets, termoBusca]);

  /**
   * Abre a confirmacao de exclusao para o dataset escolhido no menu de acoes.
   */
  const abrirConfirmacaoExclusao = (dataset: Dataset) => {
    setMenuAbertoId(null);
    setErroAcao(null);
    setMensagemAcao(null);
    setDatasetParaExcluir(dataset);
  };

  /**
   * Confirma a exclusao definitiva do dataset atualmente selecionado.
   */
  const confirmarExclusao = () => {
    if (!datasetParaExcluir) {
      return;
    }

    exclusaoMutation.mutate(datasetParaExcluir.id);
  };

  const semResultadosComFiltro = !isLoading && (datasets?.length ?? 0) > 0 && datasetsFiltrados.length === 0;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Meus Datasets</h1>
          <p className="text-slate-500 mt-1">Gerencie seus conjuntos de dados enviados para a plataforma.</p>
        </div>
        <Link
          to="/upload"
          className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-3 px-6 rounded-2xl shadow-lg shadow-emerald-500/20 transition-all flex items-center gap-2"
        >
          <Plus className="w-5 h-5" /> Novo Dataset
        </Link>
      </div>

      {mensagemAcao && (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
          {mensagemAcao}
        </div>
      )}

      {(erroAcao || error) && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{erroAcao ?? extrairMensagemErroApi(error, 'Nao foi possivel carregar seus datasets.')}</span>
        </div>
      )}

      <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3 bg-slate-50 px-4 py-2 rounded-xl border border-slate-200 w-full max-w-md">
            <Search className="w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={termoBusca}
              onChange={(evento) => setTermoBusca(evento.target.value)}
              placeholder="Filtrar por nome, descricao ou formato..."
              className="bg-transparent border-none outline-none text-sm text-slate-600 w-full"
            />
          </div>
          <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
            <Database className="w-4 h-4" /> Total visivel: {datasetsFiltrados.length}
          </div>
        </div>

        {isLoading ? (
          <div className="p-20 flex flex-col items-center justify-center gap-4">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-500"></div>
            <p className="text-slate-500 font-medium">Carregando seus datasets...</p>
          </div>
        ) : datasets && datasets.length > 0 && datasetsFiltrados.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-slate-50/50 text-slate-500 text-xs font-bold uppercase tracking-wider">
                  <th className="px-8 py-4">Dataset</th>
                  <th className="px-8 py-4">Formato</th>
                  <th className="px-8 py-4">Tamanho</th>
                  <th className="px-8 py-4">Data de Upload</th>
                  <th className="px-8 py-4">Acoes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {datasetsFiltrados.map((dataset) => (
                  <tr key={dataset.id} className="hover:bg-slate-50/50 transition-colors group">
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center text-slate-500 group-hover:bg-emerald-100 group-hover:text-emerald-500 transition-colors">
                          {dataset.formato === 'csv' ? <FileText className="w-5 h-5" /> : <FileSpreadsheet className="w-5 h-5" />}
                        </div>
                        <div>
                          <p className="text-sm font-bold text-slate-900">{dataset.nome}</p>
                          <p className="text-xs text-slate-500 truncate max-w-[240px]">{dataset.descricao || 'Sem descricao'}</p>
                          {dataset.metadados?.aviso_importacao && (
                            <p className="text-xs text-amber-600 mt-1 flex items-start gap-1 max-w-[360px]">
                              <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                              <span>{dataset.metadados.aviso_importacao}</span>
                            </p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-8 py-5">
                      <span className="text-xs font-bold px-2 py-1 bg-slate-100 text-slate-600 rounded-md uppercase">
                        {dataset.formato}
                      </span>
                    </td>
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-2 text-sm text-slate-600">
                        <HardDrive className="w-4 h-4 text-slate-400" />
                        {formatarTamanho(dataset.tamanho_bytes)}
                      </div>
                    </td>
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-2 text-sm text-slate-600">
                        <Calendar className="w-4 h-4 text-slate-400" />
                        {new Date(dataset.criado_em).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-3">
                        <Link
                          to={`/datasets/${dataset.id}`}
                          className="inline-flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-bold text-emerald-700 transition-colors hover:bg-emerald-100"
                          title="Ver detalhes"
                        >
                          Ver detalhes
                          <ArrowRight className="w-4 h-4" />
                        </Link>

                        <div className="relative">
                          <button
                            type="button"
                            onClick={() =>
                              setMenuAbertoId((atual) => (atual === dataset.id ? null : dataset.id))
                            }
                            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all"
                            aria-label={`Abrir acoes do dataset ${dataset.nome}`}
                          >
                            <MoreVertical className="w-5 h-5" />
                          </button>

                          {menuAbertoId === dataset.id && (
                            <div className="absolute right-0 top-12 z-20 w-52 rounded-2xl border border-slate-200 bg-white p-2 shadow-xl">
                              <Link
                                to={`/datasets/${dataset.id}`}
                                onClick={() => setMenuAbertoId(null)}
                                className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
                              >
                                <ArrowRight className="w-4 h-4" />
                                Ver detalhes
                              </Link>
                              <button
                                type="button"
                                onClick={() => abrirConfirmacaoExclusao(dataset)}
                                className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
                              >
                                <Trash2 className="w-4 h-4" />
                                Excluir dataset
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : semResultadosComFiltro ? (
          <div className="p-20 flex flex-col items-center justify-center text-center gap-4">
            <div className="w-20 h-20 bg-slate-50 rounded-3xl flex items-center justify-center text-slate-300">
              <Search className="w-10 h-10" />
            </div>
            <div>
              <p className="text-slate-900 font-bold text-lg">Nenhum dataset corresponde ao filtro</p>
              <p className="text-slate-500 text-sm mt-1">Ajuste o termo de busca para visualizar os datasets cadastrados.</p>
            </div>
          </div>
        ) : (
          <div className="p-20 flex flex-col items-center justify-center text-center gap-4">
            <div className="w-20 h-20 bg-slate-50 rounded-3xl flex items-center justify-center text-slate-300">
              <Database className="w-10 h-10" />
            </div>
            <div>
              <p className="text-slate-900 font-bold text-lg">Nenhum dataset encontrado</p>
              <p className="text-slate-500 text-sm mt-1">Comece enviando seu primeiro conjunto de dados para analise.</p>
            </div>
            <Link
              to="/upload"
              className="mt-4 bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-3 px-8 rounded-2xl shadow-lg shadow-emerald-500/20 transition-all"
            >
              Fazer Upload Agora
            </Link>
          </div>
        )}
      </div>

      <ModalConfirmacaoExclusaoDataset
        nomeDataset={datasetParaExcluir?.nome ?? ''}
        aberto={Boolean(datasetParaExcluir)}
        carregando={exclusaoMutation.isPending}
        erro={erroAcao}
        onConfirmar={confirmarExclusao}
        onFechar={() => {
          if (exclusaoMutation.isPending) {
            return;
          }
          setErroAcao(null);
          setDatasetParaExcluir(null);
        }}
      />
    </div>
  );
};

export default ListagemDatasets;
