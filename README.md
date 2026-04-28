# AnomalyDetect

Aplicação web para detecção de anomalias em arquivos CSV, desenvolvida como Trabalho de Conclusão de Curso (TCC) para a UNIVESP.

O sistema permite que o usuário faça upload de um arquivo CSV, selecione colunas e modelos de detecção, e receba um relatório com as anomalias encontradas — exportável em PDF ou CSV.

---

## Funcionalidades

- Upload de arquivos CSV com detecção automática de separador e encoding
- Seleção de colunas numéricas e categóricas para análise
- Execução de múltiplos algoritmos de detecção de anomalias em paralelo
- Relatório interativo com gráficos (Recharts)
- Exportação do relatório em PDF e do dataset tratado em CSV
- Limpeza automática de arquivos com mais de 10 minutos no storage

---

## Modelos disponíveis

**Numéricos**
| Modelo | Descrição |
|---|---|
| Z-Score | Desvio padrão em relação à média |
| IQR | Intervalo interquartílico |
| MAD | Desvio absoluto mediano |
| Mahalanobis | Distância considerando correlações |
| KNN | K-vizinhos mais próximos |
| LOF | Local Outlier Factor |
| Isolation Forest | Isolamento por árvores aleatórias |
| Percentile | Corte por percentil |

**Categóricos**
| Modelo | Descrição |
|---|---|
| Frequency | Frequência relativa das categorias |
| Entropy | Entropia da distribuição |
| Chi² | Teste qui-quadrado |
| Binomial | Teste binomial |
| Association Rules | Regras de associação |
| LOF Categórico | LOF adaptado para categorias |

---

## Stack

- **Backend**: Python · FastAPI · scikit-learn · pandas · Supabase
- **Frontend**: React 19 · React Router v7 · Tailwind CSS v4 · Recharts · TypeScript

---

## Como rodar localmente

### Pré-requisitos

- Python 3.11+
- Node.js 20+
- `make` (incluso no Git Bash / MSYS2 no Windows)
- Conta no [Supabase](https://supabase.com)

---

### 1. Configure o ambiente

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp backend/example.env backend/.env
```

| Variável | Onde obter | Exemplo |
|---|---|---|
| `SUPABASE_URL` | Settings → API → Project URL | `https://xxxx.supabase.co` |
| `SUPABASE_TK` | Settings → API Keys → `service_role` | `eyJhbGci...` |
| `SUPABASE_TABLE` | Nome desejado para a tabela | `arquivos` |
| `SUPABASE_BUCKET` | Nome desejado para o bucket | `csvfiles` |
| `SUPABASE_PERSONAL_TOKEN` | [supabase.com/dashboard/account/tokens](https://supabase.com/dashboard/account/tokens) — necessário apenas na primeira execução | `sbp_...` |

---

### 2. Suba a aplicação

```bash
make dev
```

Na primeira execução o comando instala as dependências, cria a tabela e o bucket no Supabase automaticamente, e sobe os dois servidores em paralelo.

| Serviço | URL |
|---|---|
| Frontend | `http://localhost:5173` |
| Backend | `http://localhost:8000` |
| Documentação da API | `http://localhost:8000/docs` |

---

## Estrutura do projeto

```
tcc-v2/
├── backend/
│   ├── src/
│   │   ├── main.py               # Entrypoint FastAPI
│   │   ├── routes/
│   │   │   ├── file_routes.py    # Upload, consulta e deleção de arquivos
│   │   │   └── model_routes.py   # Listagem de modelos e geração de relatório
│   │   ├── services/
│   │   │   ├── numeric/          # Detectores numéricos
│   │   │   ├── categorical/      # Detectores categóricos
│   │   │   └── registry.py       # Registro e execução dos modelos
│   │   └── models/               # Schemas Pydantic e cliente Supabase
│   ├── requirements.txt
│   └── example.env
└── frontend/
    ├── app/
    │   ├── routes/               # Páginas da aplicação
    │   ├── process/              # Lógica de chamada à API
    │   └── styles/               # CSS modules + global
    ├── package.json
    └── vite.config.ts
```

---

## API — principais endpoints

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/files/upload` | Faz upload de um CSV |
| `GET` | `/api/files/{id}` | Retorna metadados de um arquivo |
| `DELETE` | `/api/files/{id}` | Remove um arquivo |
| `GET` | `/api/report/models` | Lista todos os modelos disponíveis |
| `POST` | `/api/report/generate/{file_id}` | Gera o relatório de anomalias |
| `GET` | `/api/report/pdf` | Exporta o último relatório em PDF |
| `GET` | `/api/report/cleaned` | Exporta o dataset tratado em CSV |
