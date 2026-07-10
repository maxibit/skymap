FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLCONFIGDIR=/app/runtime/cache/matplotlib \
    XDG_CACHE_HOME=/app/runtime/cache

WORKDIR /app

RUN groupadd --gid 10001 skymap \
    && useradd --uid 10001 --gid skymap --create-home skymap

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY static ./static
RUN mkdir -p /app/data /app/runtime/cache \
    && chown -R skymap:skymap /app

USER skymap
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
