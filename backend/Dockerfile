FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema necessárias para algumas libs de data science
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do backend
COPY . .

# Expõe a porta do FastAPI
EXPOSE 8000

# Comando para rodar o servidor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
