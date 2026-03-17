FROM node:20-slim

WORKDIR /app

# Copia arquivos de dependências
COPY package*.json ./

# Instala dependências
RUN npm install

# Copia o código do frontend
COPY . .

# Expõe a porta do Vite (configurada para 3000)
EXPOSE 3000

# Comando para rodar o servidor de desenvolvimento
CMD ["npm", "run", "dev"]
