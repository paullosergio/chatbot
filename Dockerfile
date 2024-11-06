# Dockerfile para o serviço unificado (app)
FROM python:3.12.4

WORKDIR /app

# Instala o Poetry e dependências
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    export PATH="/root/.local/bin:$PATH"

# Adiciona Poetry ao PATH e define para não criar ambiente virtual
ENV PATH="/root/.local/bin:$PATH"
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PYTHONPATH="${PYTHONPATH}:/app/backend"

# Copia os arquivos de dependências do Poetry
COPY ./pyproject.toml ./poetry.lock ./

# Instala as dependências com Poetry
RUN poetry install --no-root

# Copia o código do aplicativo
COPY . .

# Copia o script de inicialização
COPY start_services.sh /app/start_services.sh
RUN chmod +x /app/start_services.sh

# Define o comando para rodar o frontend e backend
CMD ["./start_services.sh"]
