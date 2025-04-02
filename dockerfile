FROM python:3.11-alpine

RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev

# Рабочая директория
WORKDIR /app

# Копируем зависимости отдельно для кэширования
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь проект (исключения в .dockerignore)
COPY . .

# Production-оптимизации
ENV PYTHONPATH=/app \
    PROMETHEUS_MULTIPROC_DIR=/tmp \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1


CMD uvicorn app.main:app --host 0.0.0.0 --port 8000