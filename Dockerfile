# Dockerfile
FROM python:3.11-slim as base

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base as api
COPY src /app/src
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base as ui
COPY src /app/src
CMD ["streamlit", "run", "src/ui/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]