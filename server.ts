/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import 'dotenv/config';

import { ChildProcess, spawn } from 'child_process';
import express from 'express';
import { existsSync } from 'fs';
import { createProxyMiddleware } from 'http-proxy-middleware';
import { Server } from 'http';
import net from 'net';
import path from 'path';
import { createServer as createViteServer } from 'vite';

/**
 * Resolve o interpretador Python mais adequado, priorizando o ambiente virtual local do projeto.
 */
function obterComandoPython(): string {
  if (process.env.COMANDO_PYTHON?.trim()) {
    return process.env.COMANDO_PYTHON.trim();
  }

  const candidatoVenv =
    process.platform === 'win32'
      ? path.join(process.cwd(), '.venv', 'Scripts', 'python.exe')
      : path.join(process.cwd(), '.venv', 'bin', 'python');

  if (existsSync(candidatoVenv)) {
    return candidatoVenv;
  }

  return process.platform === 'win32' ? 'python' : 'python3';
}

/**
 * Aguarda um pequeno intervalo entre tentativas de verificacao.
 */
function aguardar(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Verifica se uma porta TCP especifica esta livre para uso no host informado.
 */
function portaEstaLivre(porta: number, host: string): Promise<boolean> {
  return new Promise((resolve) => {
    const servidorTeste = net.createServer();

    servidorTeste.once('error', () => {
      resolve(false);
    });

    servidorTeste.once('listening', () => {
      servidorTeste.close(() => resolve(true));
    });

    servidorTeste.listen(porta, host);
  });
}

/**
 * Procura a primeira porta disponivel a partir de uma porta inicial.
 */
async function encontrarPortaDisponivel(
  portaInicial: number,
  host: string,
  maxTentativas: number = 50
): Promise<number> {
  for (let deslocamento = 0; deslocamento < maxTentativas; deslocamento += 1) {
    const portaAtual = portaInicial + deslocamento;

    if (await portaEstaLivre(portaAtual, host)) {
      return portaAtual;
    }
  }

  throw new Error(`Nenhuma porta livre encontrada a partir de ${portaInicial}.`);
}

/**
 * Monta a URL do endpoint de saude do backend.
 */
function obterUrlSaudeBackend(backendUrl: string): string {
  const url = new URL(backendUrl);
  url.pathname = '/';
  url.search = '';
  return url.toString();
}

/**
 * Verifica se o backend ja esta aceitando requisicoes HTTP.
 */
async function backendEstaPronto(backendUrl: string): Promise<boolean> {
  try {
    const resposta = await fetch(obterUrlSaudeBackend(backendUrl));
    return resposta.ok;
  } catch {
    return false;
  }
}

/**
 * Aguarda o backend responder ao healthcheck antes de liberar o proxy ao usuario.
 */
async function aguardarBackendPronto(backendUrl: string, tempoEsperaMs: number): Promise<void> {
  const inicio = Date.now();

  while (Date.now() - inicio < tempoEsperaMs) {
    if (await backendEstaPronto(backendUrl)) {
      return;
    }

    await aguardar(500);
  }

  throw new Error(`O backend nao respondeu ao healthcheck em ${tempoEsperaMs}ms.`);
}

/**
 * Inicia o backend FastAPI localmente quando o modo integrado estiver habilitado.
 */
function iniciarBackendIntegrado(): ChildProcess {
  const comandoPython = obterComandoPython();

  console.log(`Iniciando o backend FastAPI com o comando ${comandoPython}...`);

  const backend = spawn(
    comandoPython,
    ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
    {
      cwd: path.join(process.cwd(), 'backend'),
      stdio: 'inherit',
    }
  );

  backend.on('error', (erro) => {
    console.error('Falha ao iniciar o backend FastAPI:', erro);
  });

  return backend;
}

/**
 * Inicia o servidor HTTP do Express e converte falhas de bind em Promise rejeitada.
 */
function iniciarServidorHttp(
  app: express.Express,
  porta: number,
  host: string
): Promise<Server> {
  return new Promise((resolve, reject) => {
    const servidor = app.listen(porta, host, () => resolve(servidor));
    servidor.once('error', reject);
  });
}

async function startServer() {
  const app = express();
  const portaPreferencial = Number(process.env.PORT || 3000);
  const host = process.env.HOST || '0.0.0.0';
  const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
  const iniciarBackend = process.env.INICIAR_BACKEND_INTEGRADO !== 'false';
  const tempoEsperaBackendMs = Number(process.env.TEMPO_ESPERA_BACKEND_MS || 30000);
  const processoBackend = iniciarBackend ? iniciarBackendIntegrado() : null;

  /**
   * Encerra o backend integrado junto com o servidor principal.
   */
  const encerrar = () => {
    if (processoBackend && !processoBackend.killed) {
      processoBackend.kill();
    }
  };

  process.on('SIGINT', () => {
    encerrar();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    encerrar();
    process.exit(0);
  });

  if (iniciarBackend) {
    console.log('Aguardando o backend ficar pronto antes de liberar o proxy...');
    try {
      await aguardarBackendPronto(backendUrl, tempoEsperaBackendMs);
    } catch (erro) {
      encerrar();
      throw erro;
    }
  }

  app.use(
    '/api',
    createProxyMiddleware({
      target: backendUrl,
      changeOrigin: true,
      proxyTimeout: tempoEsperaBackendMs,
      timeout: tempoEsperaBackendMs,
      /**
       * Reaplica o prefixo /api, pois o Express remove o path montado antes de delegar ao proxy.
       */
      pathRewrite: (pathAtual) => `/api${pathAtual}`,
      on: {
        error: (erro, _req, res) => {
          console.error('Falha ao encaminhar requisicao para o backend:', erro.message);

          if ('writeHead' in res && 'end' in res) {
            if (!res.headersSent) {
              res.writeHead(503, { 'Content-Type': 'application/json; charset=utf-8' });
            }

            res.end(
              JSON.stringify({
                detail: 'O backend ainda nao esta disponivel. Aguarde alguns segundos e tente novamente.',
              })
            );
          }
        },
      },
    })
  );

  if (process.env.NODE_ENV !== 'production') {
    const hmrHabilitado = process.env.DISABLE_HMR !== 'true';

    if (hmrHabilitado) {
      const hostHmr = process.env.VITE_HMR_HOST || '127.0.0.1';
      const portaHmrInicial = Number(process.env.VITE_HMR_PORT || 24678);
      const portaHmrDisponivel = await encontrarPortaDisponivel(portaHmrInicial, hostHmr);

      process.env.VITE_HMR_HOST = hostHmr;
      process.env.VITE_HMR_PORT = String(portaHmrDisponivel);

      console.log(`Canal HMR configurado em ws://${hostHmr}:${portaHmrDisponivel}`);
    }

    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (_req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  const portaDisponivel = await encontrarPortaDisponivel(portaPreferencial, host);

  if (portaDisponivel !== portaPreferencial) {
    console.warn(
      `Porta ${portaPreferencial} ocupada. Servidor Full-Stack sera iniciado automaticamente na porta ${portaDisponivel}.`
    );
  }

  try {
    await iniciarServidorHttp(app, portaDisponivel, host);
  } catch (erro) {
    encerrar();
    throw erro;
  }

  console.log(`Servidor Full-Stack rodando em http://localhost:${portaDisponivel}`);
  console.log(`Proxy configurado: /api -> ${backendUrl}`);
  if (!iniciarBackend) {
    console.log('Inicializacao integrada do backend desativada por configuracao.');
  }
}

startServer().catch((erro) => {
  console.error('Erro ao iniciar o servidor:', erro);
  process.exit(1);
});
