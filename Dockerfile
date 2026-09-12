FROM python:3.12-slim

ENV MPLBACKEND=Agg \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SILHOUETTE_CARD_MAKER_PATH=/opt/silhouette-card-maker

WORKDIR /app

COPY vendor/silhouette-card-maker /opt/silhouette-card-maker
COPY pyproject.toml LICENSE ./
COPY app ./app

RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-server-header"]
