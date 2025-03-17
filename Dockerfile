# Первый этап: установка зависимостей
FROM python:3.11 AS builder
WORKDIR /app

# Устанавливаем зависимости в виртуальное окружение
COPY requirements.txt .
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# Второй этап: минимальный образ
FROM python:3.11-slim AS runner
WORKDIR /app

# Копируем только код и зависимости из builder-а
COPY --from=builder /venv /venv
COPY . .

# Используем минимальный Python с виртуальным окружением
ENV PATH="/venv/bin:$PATH"

CMD ["python"]
