/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export interface Usuario {
  id: number;
  nome: string;
  email: string;
  esta_ativo: boolean;
  criado_em: string;
  atualizado_em: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface MetadadosColuna {
  nome: string;
  tipo: string;
  valores_nulos: number;
  percentual_nulos: number;
  estatisticas: {
    min?: number;
    max?: number;
    media?: number;
    mediana?: number;
    desvio_padrao?: number;
  };
}

export interface MetadadosDataset {
  colunas: MetadadosColuna[];
  total_linhas: number;
  linhas_descartadas?: number;
  linhas_com_problema?: number[];
  aviso_importacao?: string;
  codificacao?: string | null;
  separador?: string | null;
}

export interface Dataset {
  id: number;
  nome: string;
  descricao?: string;
  formato: string;
  tamanho_bytes: number;
  metadados: MetadadosDataset;
  usuario_id: number;
  criado_em: string;
}

export interface ResultadoResumo {
  total_registros: number;
  total_anomalias: number;
  percentual_anomalias: number;
  score_medio: number;
  score_maximo: number;
  interpretacao_geral?: string;
  parametros_utilizados?: Record<string, any>;
  tipos_anomalia_encontrados?: TipoAnomaliaEncontrada[];
  dicionario_tipos_anomalia?: Record<string, DicionarioTipoAnomalia>;
  anomalias_detalhadas?: AnomaliaDetalhada[];
  erro?: string;
}

export interface DicionarioTipoAnomalia {
  nome: string;
  descricao: string;
  criterio: string;
  algoritmo: string;
}

export interface TipoAnomaliaEncontrada {
  codigo: string;
  nome: string;
  quantidade: number;
  percentual: number;
  descricao: string;
  criterio: string;
}

export interface ColunaRelevanteAnomalia {
  coluna: string;
  valor_original: string | number | null;
  valor_analisado?: number | null;
  score_coluna?: number | null;
  direcao?: string;
  media_referencia?: number | null;
  desvio_padrao_referencia?: number | null;
  q1_referencia?: number | null;
  q3_referencia?: number | null;
  iqr_referencia?: number | null;
  mediana_referencia?: number | null;
  escala_referencia?: number | null;
  limite_inferior?: number | null;
  limite_superior?: number | null;
  motivo: string;
}

export interface AnomaliaDetalhada {
  indice_original: number;
  localizacao: string;
  score: number;
  tipo_principal: string;
  tipo_principal_nome: string;
  justificativa: string;
  dados_registro: Record<string, string | number | null>;
  colunas_relevantes: ColunaRelevanteAnomalia[];
}

export interface Analise {
  id: number;
  nome: string;
  algoritmo: string;
  tipo_algoritmo: string;
  dataset_id: number;
  colunas_selecionadas: string[];
  parametros: Record<string, any>;
  status: 'pendente' | 'processando' | 'concluido' | 'erro';
  resultado_resumo?: ResultadoResumo;
  caminho_resultado_csv?: string;
  criado_em: string;
}

export interface CriarAnaliseInput {
  nome: string;
  algoritmo: string;
  tipo_algoritmo: string;
  dataset_id: number;
  colunas_selecionadas: string[];
  parametros?: Record<string, any>;
}

export interface TipoRelatorio {
  id: string;
  nome: string;
  descricao: string;
}
