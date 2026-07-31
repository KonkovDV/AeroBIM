# ---------- build ----------
FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de AS builder

WORKDIR /build

COPY pyproject.toml requirements-lock.txt ./
COPY src/ src/
RUN pip install --no-cache-dir --require-hashes --prefix=/install -r requirements-lock.txt \
    && pip install --no-cache-dir --prefix=/install --no-deps .

# ---------- production ----------
FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de

LABEL org.opencontainers.image.source="https://github.com/KonkovDV/AeroBIM"
LABEL org.opencontainers.image.description="AeroBIM cross-modal BIM validation backend"
# SPDX expression covers own code (MIT) plus mandatory third-party terms:
# Core PDF path is permissive (pypdfium2 Apache/BSD + pdfminer.six MIT + Pillow).
# IfcOpenShell/IfcTester are LGPL-3.0-or-later. Optional pdf-agpl (PyMuPDF) is NOT
# in the production image. SSOT: audit/dependency_license_inventory.json
LABEL org.opencontainers.image.licenses="MIT AND LGPL-3.0-or-later AND Apache-2.0 AND BSD-3-Clause"

RUN groupadd -r aerobim && useradd -r -g aerobim -s /sbin/nologin aerobim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder /build/src/ src/
# LOIN export-enrichment metadata lives in repo samples/ (outside this build
# context) and is NOT shipped: the resolver fail-softs to 'no LOIN metadata'
# with a visible degrade flag (verdict-neutral enrichment only). Mount
# /samples/benchmarks/loin-rule-metadata.json to enable it in containers.

RUN mkdir -p var/reports && chown -R aerobim:aerobim /app

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
