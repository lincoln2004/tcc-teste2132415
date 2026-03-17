/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQueryClient } from '@tanstack/react-query';
import * as z from 'zod';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  FileText,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  FileSpreadsheet,
  Info,
} from 'lucide-react';
import { datasetServico } from '../servicos/datasetServico';
import { extrairMensagemErroApi } from '../servicos/api';
import { Dataset } from '../tipos';

const uploadSchema = z.object({
  nome: z.string().min(3, 'O nome deve ter no minimo 3 caracteres'),
  descricao: z.string().max(500, 'A descricao deve ter no maximo 500 caracteres').optional(),
});

type UploadFormData = z.infer<typeof uploadSchema>;

const UploadDataset: React.FC = () => {
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UploadFormData>({
    resolver: zodResolver(uploadSchema),
  });

  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'text/csv' || file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
      setArquivo(file);
      setErro(null);
    } else {
      setErro('Formato de arquivo invalido. Use CSV ou Excel.');
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setArquivo(file);
      setErro(null);
    }
  };

  /**
   * Envia o arquivo para a API e sincroniza o cache local antes de navegar para a listagem.
   */
  const onSubmit = async (data: UploadFormData) => {
    if (!arquivo) {
      setErro('Por favor, selecione um arquivo.');
      return;
    }

    setCarregando(true);
    setErro(null);
    try {
      const datasetCriado = await datasetServico.upload(data.nome, data.descricao || '', arquivo);

      queryClient.setQueryData<Dataset[]>(['datasets'], (datasetsAtuais) => {
        const listaAtual = datasetsAtuais ?? [];
        const listaSemDuplicados = listaAtual.filter((dataset) => dataset.id !== datasetCriado.id);
        return [datasetCriado, ...listaSemDuplicados];
      });

      await queryClient.invalidateQueries({ queryKey: ['datasets'] });
      navigate('/datasets');
    } catch (erroApi) {
      setErro(extrairMensagemErroApi(erroApi, 'Erro ao realizar upload do dataset.'));
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Upload de Dataset</h1>
        <p className="text-slate-500 mt-1">Envie seus dados tabulares para iniciar a deteccao de anomalias.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <form onSubmit={handleSubmit(onSubmit)} className="bg-white p-8 rounded-3xl shadow-sm border border-slate-200 space-y-6">
            {erro && (
              <div className="p-4 bg-red-50 border border-red-200 text-red-600 text-sm rounded-xl flex items-center gap-3 font-medium">
                <AlertCircle className="w-5 h-5" /> {erro}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Nome do Dataset</label>
              <input
                {...register('nome')}
                type="text"
                placeholder="Ex: Vendas 2023 - Q4"
                className={`w-full px-4 py-3 rounded-xl border ${errors.nome ? 'border-red-500' : 'border-slate-200'} focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all`}
              />
              {errors.nome && <p className="text-xs text-red-500 font-medium">{errors.nome.message}</p>}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Descricao (Opcional)</label>
              <textarea
                {...register('descricao')}
                rows={3}
                placeholder="Descreva brevemente o conteudo deste conjunto de dados..."
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all resize-none"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Arquivo</label>
              {!arquivo ? (
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={onDrop}
                  className="border-2 border-dashed border-slate-200 rounded-2xl p-12 flex flex-col items-center justify-center gap-4 hover:border-emerald-400 hover:bg-emerald-50/30 transition-all cursor-pointer group"
                  onClick={() => document.getElementById('file-input')?.click()}
                >
                  <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center text-slate-400 group-hover:bg-emerald-100 group-hover:text-emerald-500 transition-colors">
                    <Upload className="w-8 h-8" />
                  </div>
                  <div className="text-center">
                    <p className="text-slate-900 font-bold">Arraste e solte seu arquivo aqui</p>
                    <p className="text-slate-500 text-sm mt-1">Ou clique para selecionar (CSV, XLSX, XLS)</p>
                  </div>
                  <input
                    id="file-input"
                    type="file"
                    className="hidden"
                    accept=".csv, .xlsx, .xls"
                    onChange={handleFileChange}
                  />
                </div>
              ) : (
                <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center text-emerald-500 shadow-sm">
                      {arquivo.name.endsWith('.csv') ? <FileText className="w-6 h-6" /> : <FileSpreadsheet className="w-6 h-6" />}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-slate-900">{arquivo.name}</p>
                      <p className="text-xs text-slate-500">{(arquivo.size / 1024).toFixed(1)} KB</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setArquivo(null)}
                    className="p-2 text-slate-400 hover:text-red-500 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={carregando}
              className="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-4 rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-70"
            >
              {carregando ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <CheckCircle className="w-5 h-5" /> Salvar Dataset
                </>
              )}
            </button>
          </form>
        </div>

        <div className="space-y-6">
          <div className="bg-slate-900 text-white p-8 rounded-3xl shadow-xl border border-slate-800">
            <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
              <Info className="w-5 h-5 text-emerald-400" /> Dicas de Upload
            </h3>
            <ul className="space-y-4 text-sm text-slate-400">
              <li className="flex gap-3">
                <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full mt-2 shrink-0"></div>
                Certifique-se de que a primeira linha contem os nomes das colunas.
              </li>
              <li className="flex gap-3">
                <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full mt-2 shrink-0"></div>
                O sistema suporta arquivos de ate 50MB.
              </li>
              <li className="flex gap-3">
                <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full mt-2 shrink-0"></div>
                Dados numericos sao ideais para a maioria dos algoritmos estatisticos.
              </li>
              <li className="flex gap-3">
                <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full mt-2 shrink-0"></div>
                Valores nulos serao preenchidos automaticamente com a media da coluna.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadDataset;
