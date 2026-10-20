FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY src/ ./src/
RUN mkdir -p /app/chroma_db_storage
EXPOSE 8501
CMD ["streamlit", "run", "src/app.py", "--server.address=0.0.0.0"]
