# ---------- build ----------
FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de AS builder
WORKDIR /build
COPY pyproject.toml requirements-lock.txt ./
COPY src/ src/
RUN printf '%s\n' \
      'redis==5.2.1 \' \
      '  --hash=sha256:16f2e22dff21d5125e8481515e386711a34cbec50f0e44413dd7d9c060a54e0f \' \
      '  --hash=sha256:ee7e1056b9aea0f04c6c2ed59452947f34c4940ee025f5dd83e6a6418b6989e4' \
      > /tmp/redis-requirement.txt \
    && pip install --no-cache-dir --require-hashes --prefix=/install -r requirements-lock.txt \
    && pip install --no-cache-dir --require-hashes --prefix=/install -r /tmp/redis-requirement.txt \
    && pip install --no-cache-dir --prefix=/install --no-deps .

# ---------- production ----------
FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de
LABEL org.opencontainers.image.source="https://github.com/KonkovDV/AeroBIM"
LABEL org.opencontainers.image.description="AeroBIM API and isolated IFC analyze worker"
LABEL org.opencontainers.image.licenses="MIT AND LGPL-3.0-or-later AND Apache-2.0 AND BSD-3-Clause"
RUN groupadd -r aerobim && useradd -r -g aerobim -s /sbin/nologin aerobim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --from=builder /build/src/ src/
RUN mkdir -p var/reports /data/reports /data/reports/reports /data/reports/drawing-assets \
    && chown -R aerobim:aerobim /app /data
USER aerobim
ENV AEROBIM_ENV=production \
    AEROBIM_SIGNOFF_PROFILE=production \
    AEROBIM_HOST=0.0.0.0 \
    AEROBIM_PORT=8080 \
    AEROBIM_DEBUG=false \
    AEROBIM_STORAGE_DIR=var/reports \
    PYTHONPATH=/app/src
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')" || exit 1
ENTRYPOINT ["python", "-m", "aerobim.main"]
