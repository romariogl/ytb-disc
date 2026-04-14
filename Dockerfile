# Usa uma imagem oficial do Python
FROM python:3.10-slim

# Instala o FFmpeg e dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos de requisitos e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código do bot
COPY . .

# Comando para rodar o bot
CMD ["python", "main.py"]