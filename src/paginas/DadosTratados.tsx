/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Database,
  Download,
  Loader2,
  AlertCircle,
  Table,
  Filter,
} from 'lucide-react';
import { analiseServico } from '../../servicos/analiseServico';
import { extrairMensagemErroApi } from '../../servicos/api';

interface DadoTratado {
  [key: string]: string | number | null;
}

const DadosTratados: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [paginaAtual, setPaginaAtual] = useState(1);
  const [baixandoArquivo, setBaixandoArquivo] = useState(false);
  const itensPorPagina = 50;

  const { data: analise, isLoading, error } = useQuery({
    queryKey: ['analise', id],
    queryFn: () => analiseServico.obterPorId(parseInt(id!, 10)),
    enabled: !!id,
  });

  const [dados, setDados] = useState<DadoTratado[]>([]);
  const [colunas, setColunas] = useState<string[]>([]);
  const [carregandoDados, setCarregandoDados] = useState(true);
  const [erroDados, setErroDados] = useState<string | null>(null);

  React.useEffect(() => {
    const carregarDados = async () => {
      if (!analise?.caminho_resultado_csv) return;

      setCarregandoDados(true);
      setErroDados(null);

      try {
        // Buscar o CSV diretamente via API
        const response = await fetch(`/api/v1/analises/${id}/download`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });

        if (!response.ok) {
          throw new Error('Erro ao carregar dados');
        }

        const texto = await response.text();
        const linhas = texto.split('\n').filter((linha) => linha.trim());
        
        if (linhas.length === 0) {
          setErroDados('Nenhum dado encontrado');
          return;
        }

        // Parse CSV simples
        const cabecalho = linhas[0].split(',').map((h) => h.trim().replace(/"/g, ''));
        setColunas(cabecalho);

        const dadosParseados: DadoTratado[] = [];
        for (let i = 1; i < Math.min(linhas.length, 1000); i++) {
          const valores = linhas[i].split(',').map((v) => v.trim().replace(/"/g, ''));
          const registro: DadoTratado = {};
          
          cabecalho.forEach((col, idx) => {
            const valor = valores[idx];
            // Tentar converter para numero se possivel
            const num = parseFloat(valor);
            registro[col] = isNaN(num) ? valor : num;
          });
          
          dadosParseados.push(registro);
        }

        setDados(dadosParseados);
      } catch (erro) {
        setErroDados(extrairMensagemErroApi(erro, 'Erro ao carregar dados tratados.'));
      } finally {
        setCarregandoDados(false);
      }
    };

    carregarDados();
  }, [analise, id]);

  const handleDownload = async () => {
    if (!analise) return;

    setBaixandoArquivo(true);
    try {
      await analiseServico.baixarResultado(analise.id);
    } catch (erroApi) {
      setErroDados(extrairMensagemErroApi(erroApi, 'Não foi possível baixar o arquivo.'));
    } finally {
      setBaixandoArquivo(false);
    }
  };

  if (isLoading || carregandoDados) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center gap-4">
        <Loader2 className="w-12 h-12 text-emerald-500 animate-spin" />
        <div className="text-center">
          <h2 className="text-xl font-bold text-slate-900">Carregando dados...</h2>
          <p className="text-slate-500 text-sm mt-1">Estamos recuperando os dados tratados da analise.</p>
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
          <p className="text-slate-500 text-sm mt-1">Não foi possível recuperar os resultados desta analise.</p>
        </div>
        <Link to="/historico" className="text-emerald-600 font-bold hover:underline flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Voltar para o historico
        </Link>
      </div>
    );
  }

  const totalPaginas = Math.ceil(dados.length / itensPorPagina);
  const dadosPagina = dados.slice(
    (paginaAtual - 1) * itensPorPagina,
    paginaAtual * itensPorPagina
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(`/analise/resultado/${id}`)}
            className="p-2 hover:bg-slate-100 rounded-xl transition-colors text-slate-400"
          >
            <ArrowLeft className="w-6 h-6" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Dados Tratados</h1>
            <div className="flex items-center gap-3 mt-1 flex-wrap">
              <span className="text-xs font-bold px-2 py-0.5 bg-slate-100 text-slate-600 rounded-md uppercase">
                {analise.algoritmo}
              </span>
              <p className="text-slate-500 text-sm">
                {dados.length} registros • {colunas.length} colunas
              </p>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={handleDownload}
          disabled={baixandoArquivo}
          className="bg-slate-900 hover:bg-slate-800 text-white font-bold py-3 px-6 rounded-2xl shadow-lg transition-all flex items-center gap-2 disabled:opacity-60"
        >
          {baixandoArquivo ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />}
          Exportar CSV Completo
        </button>
      </div>

      {erroDados && (
        <div className="bg-red-50 border border-red-200 p-4 rounded-2xl text-red-700 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{erroDados}</span>
        </div>
      )}

      <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-200 flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center">
            <Table className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">Visualizacao dos Dados</h3>
            <p className="text-sm text-slate-500">
              Mostrando {dadosPagina.length} de {dados.length} registros (pagina {paginaAtual} de {totalPaginas})
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                {colunas.map((coluna) => (
                  <th
                    key={coluna}
                    className="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider whitespace-nowrap"
                  >
                    <div className="flex items-center gap-2">
                      <Filter className="w-3 h-3" />
                      {coluna}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {dadosPagina.map((registro, idx) => (
                <tr key={idx} className="hover:bg-slate-50 transition-colors">
                  {colunas.map((coluna) => (
                    <td key={coluna} className="px-4 py-3 text-sm text-slate-700 whitespace-nowrap">
                      {registro[coluna] !== null && registro[coluna] !== undefined
                        ? String(registro[coluna])
                        : '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {totalPaginas > 1 && (
          <div className="p-4 border-t border-slate-200 flex items-center justify-between">
            <button
              onClick={() => setPaginaAtual((p) => Math.max(1, p - 1))}
              disabled={paginaAtual === 1}
              className="px-4 py-2 text-sm font-bold text-slate-600 hover:bg-slate-100 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Anterior
            </button>
            <span className="text-sm text-slate-500">
              Pagina {paginaAtual} de {totalPaginas}
            </span>
            <button
              onClick={() => setPaginaAtual((p) => Math.min(totalPaginas, p + 1))}
              disabled={paginaAtual === totalPaginas}
              className="px-4 py-2 text-sm font-bold text-slate-600 hover:bg-slate-100 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Proxima
            </button>
          </div>
        )}
      </div>

      <div className="pt-2">
        <Link
          to={`/analise/${id}/relatorios`}
          className="inline-flex items-center gap-2 text-emerald-600 font-bold hover:underline"
        >
          <Database className="w-4 h-4" /> Gerar Relatorios Especializados
        </Link>
      </div>
    </div>
  );
};

export default DadosTratados;
