/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { AlertTriangle, Loader2, Trash2, X } from 'lucide-react';

interface ModalConfirmacaoExclusaoHistoricoProps {
  aberto: boolean;
  carregando: boolean;
  quantidadeAnalises: number;
  erro?: string | null;
  onConfirmar: () => void;
  onFechar: () => void;
}

const ModalConfirmacaoExclusaoHistorico: React.FC<ModalConfirmacaoExclusaoHistoricoProps> = ({
  aberto,
  carregando,
  quantidadeAnalises,
  erro,
  onConfirmar,
  onFechar,
}) => {
  if (!aberto) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4">
      <div className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-8 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-red-100 text-red-600">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Excluir todo o historico</h2>
              <p className="mt-1 text-sm text-slate-500">
                Esta acao remove todas as analises salvas e tambem apaga os CSVs gerados.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onFechar}
            className="rounded-xl p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
            aria-label="Fechar confirmacao"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-6 rounded-2xl border border-red-100 bg-red-50 p-4">
          <p className="text-sm text-red-700">
            Voce esta prestes a excluir <span className="font-bold">{quantidadeAnalises}</span> analise(s) do historico.
          </p>
        </div>

        {erro && (
          <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {erro}
          </div>
        )}

        <div className="mt-8 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onFechar}
            disabled={carregando}
            className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-bold text-slate-600 transition-colors hover:bg-slate-50 disabled:opacity-60"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirmar}
            disabled={carregando}
            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-red-600 px-5 py-3 text-sm font-bold text-white transition-colors hover:bg-red-700 disabled:opacity-60"
          >
            {carregando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
            Confirmar exclusao
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModalConfirmacaoExclusaoHistorico;
