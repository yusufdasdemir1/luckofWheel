FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Windows'ta CRLF ile kaydedilmiş olsa bile script çalışsın
RUN sed -i 's/\r$//' docker-entrypoint.sh \
    && chmod +x docker-entrypoint.sh \
    && adduser --system --uid 1001 app \
    && chown -R app /app

USER app
EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
