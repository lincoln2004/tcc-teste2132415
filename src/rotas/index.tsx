/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

const LayoutPrivado = lazy(() => import('../componentes/layout/LayoutPrivado'));
const Login = lazy(() => import('../paginas/Login'));
const Cadastro = lazy(() => import('../paginas/Cadastro'));
const HistoricoAnalises = lazy(() => import('../paginas/HistoricoAnalises'));
const UploadDataset = lazy(() => import('../paginas/UploadDataset'));
const ListagemDatasets = lazy(() => import('../paginas/ListagemDatasets'));
const DetalhesDataset = lazy(() => import('../paginas/DetalhesDataset'));
const CriarAnalise = lazy(() => import('../paginas/CriarAnalise'));
const ResultadoAnalise = lazy(() => import('../paginas/ResultadoAnalise'));
const DadosTratados = lazy(() => import('../paginas/DadosTratados'));
const GerarRelatorios = lazy(() => import('../paginas/GerarRelatorios'));

const AppRoutes: React.FC = () => {
  return (
    <BrowserRouter>
      <Suspense
        fallback={
          <div className="min-h-screen bg-slate-50 flex items-center justify-center">
            <div className="flex flex-col items-center gap-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
              <p className="text-sm font-medium text-slate-500">Carregando interface...</p>
            </div>
          </div>
        }
      >
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/cadastro" element={<Cadastro />} />

          <Route element={<LayoutPrivado />}>
            <Route path="/" element={<Navigate to="/historico" replace />} />
            <Route path="/upload" element={<UploadDataset />} />
            <Route path="/datasets" element={<ListagemDatasets />} />
            <Route path="/datasets/:id" element={<DetalhesDataset />} />
            <Route path="/analise/nova" element={<CriarAnalise />} />
            <Route path="/analise/resultado/:id" element={<ResultadoAnalise />} />
            <Route path="/analise/:id/dados-tratados" element={<DadosTratados />} />
            <Route path="/analise/:id/relatorios" element={<GerarRelatorios />} />
            <Route path="/historico" element={<HistoricoAnalises />} />
          </Route>

          <Route path="*" element={<Navigate to="/historico" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
};

export default AppRoutes;
