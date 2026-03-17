/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  Database,
  Settings,
  Columns,
  Play,
  Loader2,
  AlertCircle,
  Info,
} from 'lucide-react';
import { datasetServico } from '../servicos/datasetServico';
import { analiseServico } from '../servicos/analiseServico';
import { extrairMensagemErroApi } from '../servicos/api';
import { Dataset } from '../tipos';

const CriarAnalise: React.FC = () => {
  const navigate = useNavigate();
  const [datasetSelecionado, setDatasetSelecionado] = useState<Dataset | null>(null);
  const [colunasSelecionadas, setColunasSelecionadas] = useState<string[]>([]);
  const [algoritmo, setAlgoritmo] = useState('isolation_forest');
  const [nome, setNome] = useState('');
  const [erro, setErro] = useState<string | null>(null);

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetServico.listar,
  });

  const mutation = useMutation({
    mutationFn: analiseServico.executar,
    onSuccess: (data) => {
      navigate(`/analise/resultado/${data.id}`);
    },
    onError: (erroApi) => {
      setErro(extrairMensagemErroApi(erroApi, 'Erro ao iniciar analise.'));
    },
  });

  const handleDatasetChange = (id: string) => {
    const ds = datasets?.find((dataset) => dataset.id === parseInt(id)) || null;
    setDatasetSelecionado(ds);
    setColunasSelecionadas([]);
    setErro(null);
    if (ds && !nome) {
      setNome(`Analise - ${ds.nome}`);
    }
  };

  const toggleColuna = (coluna: string) => {
    setErro(null);
    setColunasSelecionadas((colunasAtuais) =>
      colunasAtuais.includes(coluna)
        ? colunasAtuais.filter((item) => item !== coluna)
        : [...colunasAtuais, coluna]
    );
  };

  const handleExecutar = () => {
    if (!datasetSelecionado || colunasSelecionadas.length === 0 || !nome) {
      setErro('Preencha todos os campos obrigatorios.');
      return;
    }

    const tipoAlgoritmo = ['zscore', 'iqr'].includes(algoritmo) ? 'estatistico' : 'machine_learning';

    mutation.mutate({
      nome,
      algoritmo,
      tipo_algoritmo: tipoAlgoritmo,
      dataset_id: datasetSelecionado.id,
      colunas_selecionadas: colunasSelecionadas,
      parametros: {},
    });
  };

  const algoritmos = [
    { id: 'isolation_forest', nome: 'Isolation Forest', tipo: 'Machine Learning', desc: 'Ideal para dados multivariados e alta dimensao.' },
    { id: 'lof', nome: 'Local Outlier Factor', tipo: 'Machine Learning', desc: 'Detecta anomalias baseadas na densidade local.' },
    { id: 'zscore', nome: 'Z-Score', tipo: 'Estatistico', desc: 'Baseado no desvio padrao e adequado a distribuicoes mais regulares.' },
    { id: 'iqr', nome: 'IQR', tipo: 'Estatistico', desc: 'Robusto a outliers extremos por usar quartis.' },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Nova Analise</h1>
        <p className="text-slate-500 mt-1">Configure os parametros para detectar anomalias em seus dados.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <section className="bg-white p-8 rounded-3xl shadow-sm border border-slate-200 space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center">
                <Database className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-bold text-slate-900">1. Selecao de Dados</h2>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700">Nome da Analise</label>
                <input
                  type="text"
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  placeholder="Ex: Deteccao de Fraudes - Vendas Outubro"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700">Escolher Dataset</label>
                <select
                  onChange={(e) => handleDatasetChange(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all bg-white"
                >
                  <option value="">Selecione um dataset...</option>
                  {datasets?.map((dataset) => (
                    <option key={dataset.id} value={dataset.id}>
                      {dataset.nome} ({dataset.formato.toUpperCase()})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </section>

          <section className="bg-white p-8 rounded-3xl shadow-sm border border-slate-200 space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-amber-100 text-amber-600 rounded-xl flex items-center justify-center">
                <Settings className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-bold text-slate-900">2. Metodo de Deteccao</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {algoritmos.map((alg) => (
                <button
                  key={alg.id}
                  onClick={() => setAlgoritmo(alg.id)}
                  className={`p-5 rounded-2xl border-2 text-left transition-all ${
                    algoritmo === alg.id
                      ? 'border-emerald-500 bg-emerald-50/50 ring-4 ring-emerald-500/10'
                      : 'border-slate-100 hover:border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-slate-900">{alg.nome}</span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                        alg.tipo === 'Estatistico' ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600'
                      }`}
                    >
                      {alg.tipo}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed">{alg.desc}</p>
                </button>
              ))}
            </div>
          </section>

          <section className="bg-white p-8 rounded-3xl shadow-sm border border-slate-200 space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center">
                <Columns className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-bold text-slate-900">3. Selecao de Colunas</h2>
            </div>

            {!datasetSelecionado ? (
              <div className="p-12 text-center border-2 border-dashed border-slate-100 rounded-2xl">
                <p className="text-slate-400 text-sm italic">Selecione um dataset no passo 1 para visualizar as colunas disponiveis.</p>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-sm text-slate-500">Selecione as colunas numericas usadas para identificar anomalias:</p>
                <p className="text-xs text-slate-400">
                  Valores monetarios e numeros com virgula decimal sao convertidos automaticamente. Colunas textuais puras serao rejeitadas pelo backend.
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {datasetSelecionado.metadados.colunas.map((coluna) => (
                    <button
                      key={coluna.nome}
                      onClick={() => toggleColuna(coluna.nome)}
                      className={`p-3 rounded-xl border text-sm font-medium transition-all flex items-center justify-between ${
                        colunasSelecionadas.includes(coluna.nome)
                          ? 'bg-emerald-500 text-white border-emerald-500 shadow-md shadow-emerald-500/20'
                          : 'bg-white text-slate-600 border-slate-200 hover:border-emerald-300'
                      }`}
                    >
                      <span className="truncate">{coluna.nome}</span>
                      <span className="text-[10px] opacity-60 ml-2">
                        {coluna.tipo.includes('float') || coluna.tipo.includes('int') ? 'NUM' : 'CAT'}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </section>
        </div>

        <div className="space-y-6">
          <div className="bg-slate-900 text-white p-8 rounded-3xl shadow-xl border border-slate-800 sticky top-24">
            <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
              <Activity className="w-5 h-5 text-emerald-400" /> Resumo da Configuracao
            </h3>

            <div className="space-y-4 mb-8">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Dataset:</span>
                <span className="font-bold text-emerald-400">{datasetSelecionado?.nome || '-'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Algoritmo:</span>
                <span className="font-bold text-emerald-400">{algoritmos.find((item) => item.id === algoritmo)?.nome}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Colunas:</span>
                <span className="font-bold text-emerald-400">{colunasSelecionadas.length} selecionadas</span>
              </div>
            </div>

            {erro && (
              <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" /> {erro}
              </div>
            )}

            <button
              onClick={handleExecutar}
              disabled={mutation.isPending || !datasetSelecionado || colunasSelecionadas.length === 0}
              className="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-4 rounded-2xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {mutation.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Play className="w-5 h-5 fill-current" /> Executar Analise
                </>
              )}
            </button>

            <div className="mt-6 pt-6 border-t border-slate-800 flex items-start gap-3">
              <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
              <p className="text-[10px] text-slate-500 leading-relaxed">
                O processamento pode levar alguns segundos dependendo do tamanho do dataset e do algoritmo escolhido.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CriarAnalise;
