
# 1. Imagem base do Python
FROM python:3.13-slim

# 2. Diretório de trabalho no contêiner
WORKDIR /app

# 3. Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. Instalação de dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Instalação das bibliotecas Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar o restante dos arquivos do projeto
COPY . .

# 7. Porta exposta pela API
EXPOSE 8000

# 8. Comando para rodar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]