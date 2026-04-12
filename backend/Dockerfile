# ---------- build ----------
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml ./
COPY src/ src/
RUN pip install --no-cache-dir --prefix=/install ".[vision]"

# ---------- production ----------
FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/KonkovDV/AeroBIM"
LABEL org.opencontainers.image.description="AeroBIM cross-modal BIM validation backend"
LABEL org.opencontainers.image.licenses="MIT"

RUN groupadd -r aerobim && useradd -r -g aerobim -s /sbin/nologin aerobim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder /build/src/ src/

RUN mkdir -p var/reports && chown -R aerobim:aerobim /app

USER aerobim

ENV AEROBIM_ENV=production \
    AEROBIM_HOST=0.0.0.0 \
    AEROBIM_PORT=8080 \
    AEROBIM_DEBUG=false \
    AEROBIM_STORAGE_DIR=var/reports \
    PYTHONPATH=/app/src

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')" || exit 1

ENTRYPOINT ["python", "-m", "aerobim.main"]
