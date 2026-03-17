# Manual de Uso

## 1. Visao geral

O **AnomalyDetect** e uma aplicacao para **detectar anomalias em planilhas**.

Na pratica, o sistema permite:

- criar uma conta e fazer login
- enviar arquivos `CSV`, `XLSX` ou `XLS`
- armazenar datasets localmente
- executar analises com diferentes modelos
- visualizar um resultado descritivo
- exportar o resultado em `CSV`
- consultar e limpar o historico de analises

O armazenamento local da aplicacao e feito em:

- banco JSON: `backend/dados/banco_local.json`
- arquivos enviados e resultados: `backend/uploads`

---

## 2. Como iniciar o sistema

### 2.1. Primeira execucao

1. Instale as dependencias do frontend:

```cmd/powershell
npm install
```

2. Crie o ambiente virtual do Python:

```cmd/powershell
python -m venv .venv
```

3. Instale as dependencias do backend:

```cmd/powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

4. Crie os arquivos de ambiente com base nos exemplos:

- `.env`
- `backend/.env`

5. Inicie a aplicacao integrada:



```cmd/powershell
entrar na pasta do projeto "cd C:\Projetos\TCC"

npm run dev
```

### 2.2. Observacoes importantes

- o backend e iniciado automaticamente pelo `server.ts`
- se a porta `3000` estiver ocupada, o sistema tenta subir em outra porta livre
- o backend roda em `8000`
- o frontend usa proxy `/api` para falar com o backend

---

## 3. Como entrar no sistema
No terminal deve aparecer algo como "Servidor Full-Stack rodando em http://localhost:3001" clicar no link segurando o ctrl. Isso fará com que abra o navegador com o app em produção.

### 3.1. Criar conta

1. Acesse a tela de cadastro.
2. Informe:
- nome completo
- e-mail valido
- senha com pelo menos 8 caracteres, contendo letra e numero
- confirmacao da senha
3. Clique em **Criar Minha Conta**.
4. Em caso de sucesso, o sistema redireciona para a tela de login.

### 3.2. Fazer login

1. Na tela de login, informe:
- e-mail
- senha
2. Clique em **Entrar**.
3. Depois da autenticacao, o sistema abre a tela **Historico**.

### 3.3. Sair da conta

- Use o botao **Sair** no menu lateral.

---

## 4. Menu principal

Depois do login, o menu lateral possui as seguintes areas:

- **Historico**
- **Meus Datasets**
- **Upload Dataset**
- **Nova Analise**

---

## 5. Upload de dataset

### 5.1. O que pode ser enviado

O sistema aceita:

- `CSV`
- `XLSX`
- `XLS`

Limite atual:

- ate **50 MB**

### 5.2. Como fazer upload

1. Abra **Upload Dataset**.
2. Preencha:
- **Nome do Dataset**
- **Descricao** opcional
3. Selecione ou arraste o arquivo.
4. Clique em **Salvar Dataset**.

### 5.3. O que o sistema faz no upload

Ao salvar, o sistema:

- registra o dataset no banco JSON local
- salva o arquivo no disco
- detecta colunas, tipos e estatisticas basicas
- tenta identificar separador e codificacao do arquivo
- descarta linhas malformadas, quando necessario, e registra aviso de importacao

### 5.4. Recomendacoes para o arquivo

- a primeira linha deve conter o nome das colunas
- para analises melhores, prefira colunas numericas
- valores monetarios e numeros com virgula decimal sao convertidos automaticamente
- colunas textuais puras nao sao adequadas para os modelos numericos

---

## 6. Tela "Meus Datasets"

Essa tela lista todos os datasets enviados pelo usuario autenticado.

Para cada dataset, o sistema mostra:

- nome
- descricao
- formato
- tamanho
- data de upload
- aviso de importacao, quando houver

### 6.1. Acoes disponiveis

#### Ver detalhes

Ao clicar em **Ver detalhes**, o sistema abre uma pagina com:

- informacoes gerais do arquivo
- total de linhas importadas
- total de colunas detectadas
- codificacao e separador
- quantidade de linhas descartadas
- lista de colunas com tipos e estatisticas

#### Menu de acoes

No botao de **tres pontinhos**, estao disponiveis:

- **Ver detalhes**
- **Excluir dataset**

### 6.2. Excluir dataset

Quando um dataset e excluido, o sistema remove:

- o registro do dataset
- o arquivo enviado
- as analises relacionadas
- os arquivos de resultado gerados por essas analises

Essa exclusao e definitiva.

---

## 7. Criar uma nova analise

### 7.1. Como criar

1. Abra **Nova Analise**.
2. Informe um nome para a analise.
3. Escolha um dataset.
4. Selecione o modelo de deteccao.
5. Marque as colunas numericas que deseja analisar.
6. Clique em **Executar Analise**.

### 7.2. Modelos disponiveis

#### Z-Score

O Z-Score mede o quanto um valor esta distante da media.

Quando usar:

- quando os dados seguem um comportamento mais regular
- quando voce quer identificar valores muito altos ou muito baixos em relacao ao restante

Como interpretar:

- quanto maior o desvio em relacao a media, maior a chance de anomalia

Exemplo:

- se a maioria dos valores esta entre `10` e `20`, um valor `150` pode ser marcado como anomalia

#### IQR

O IQR usa quartis para identificar valores fora da faixa esperada.

Quando usar:

- quando os dados possuem variacao e voce quer uma abordagem robusta
- quando ha risco de valores extremos distorcerem a media

Como interpretar:

- o sistema calcula limites inferior e superior com base nos quartis
- o que fica fora desses limites pode ser anomalia

#### Isolation Forest

O Isolation Forest e um modelo de machine learning que tenta isolar registros raros.

Quando usar:

- em datasets com varias colunas numericas
- quando a anomalia depende da combinacao entre os valores, e nao de uma coluna isolada

Como interpretar:

- registros raros tendem a ser isolados mais rapidamente e recebem maior score de anomalia

#### LOF

O LOF, ou **Local Outlier Factor**, compara cada registro com seus vizinhos mais proximos.

Quando usar:

- quando voce quer encontrar anomalias locais
- quando existem grupos diferentes dentro do dataset

Como interpretar:

- um registro pode parecer normal no conjunto inteiro, mas anormal dentro da vizinhanca em que esta inserido

---

## 8. Tela de resultado da analise

Depois da execucao, o sistema abre a tela de resultado.

Essa tela mostra:

- status da analise
- algoritmo utilizado
- colunas analisadas
- parametros aplicados
- total de registros avaliados
- total de anomalias encontradas
- percentual de anomalias
- score medio e score maximo
- grafico de distribuicao entre registros normais e anomalias

### 8.1. Resultado descritivo

O sistema nao mostra apenas que existe uma anomalia. Ele tambem explica:

- **onde** ela foi encontrada
- **por que** foi marcada
- **quais colunas** mais influenciaram no alerta
- **qual foi o score** atribuido

### 8.2. Dicionario dos tipos de anomalia

Cada analise pode exibir um dicionario com:

- codigo da anomalia
- nome
- descricao
- criterio tecnico
- quantidade encontrada
- percentual no dataset

Isso ajuda a entender o significado de cada tipo de desvio encontrado.

### 8.3. Exportar CSV

Se a analise foi concluida com sucesso, o botao **Exportar CSV** fica disponivel.

O arquivo exportado inclui, alem dos dados originais:

- `anomalia_flag`
- `anomalia_score`

Esse arquivo pode ser usado para auditoria externa ou revisao manual.

---

## 9. Historico de analises

A tela **Historico** reune todas as analises feitas pelo usuario logado.

Ela permite:

- buscar por nome, algoritmo ou tipo
- filtrar por status
- filtrar por algoritmo
- reabrir resultados anteriores
- exportar o CSV de uma analise concluida
- excluir todo o historico

### 9.1. Excluir todo o historico

Ao usar **Excluir todo o historico**, o sistema remove:

- todos os registros de analises do usuario
- os arquivos CSV de resultado relacionados

Essa acao ajuda a reduzir o armazenamento local e nao pode ser desfeita.

---

## 10. Erros e comportamentos esperados

### 10.1. Cadastro

O cadastro pode falhar quando:

- o e-mail ja estiver em uso
- a senha nao cumprir os requisitos
- os campos obrigatorios estiverem invalidos

O sistema mostra a mensagem real retornada pela API.

### 10.2. Login

O login pode falhar quando:

- o e-mail nao existir
- a senha estiver incorreta
- o token estiver ausente ou expirado em acoes autenticadas

### 10.3. Upload de dataset

O upload pode apresentar aviso quando:

- o arquivo tiver linhas malformadas
- o separador estiver inconsistente
- houver colunas com dados nao numericos para analise estatistica

Em alguns casos, o sistema consegue importar mesmo assim e registra o aviso no dataset.

### 10.4. Analise

A analise pode falhar quando:

- nenhuma coluna valida for selecionada
- a coluna escolhida for textual e nao puder ser convertida
- o dataset nao tiver dados suficientes para o modelo

---

## 11. Estrutura de armazenamento local

Arquivos principais utilizados pelo sistema:

- banco local: `backend/dados/banco_local.json`
- uploads e resultados: `backend/uploads`
- logs do backend: `backend/logs/app.log`

---

## 12. Fluxo recomendado de uso

Para usar o sistema do inicio ao fim:

1. criar conta
2. fazer login
3. enviar um dataset
4. revisar o dataset em **Meus Datasets**
5. criar uma nova analise
6. escolher colunas numericas adequadas
7. executar a analise
8. interpretar os resultados
9. exportar o CSV, se necessario
10. consultar ou limpar o historico quando desejar

---

## 13. Resumo rapido

Em poucas palavras, o app serve para:

- receber planilhas
- detectar valores e comportamentos fora do padrao
- explicar de forma clara onde e por que ocorreu a anomalia
- apoiar auditoria, revisao e investigacao de dados
