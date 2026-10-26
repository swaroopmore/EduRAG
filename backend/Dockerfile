FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first so Docker can cache this layer.
COPY requirements.txt .
# CPU-only torch first (the default PyPI wheel drags in ~3 GB of CUDA libraries the
# server never uses); requirements.txt then sees torch as already satisfied.
RUN pip install --upgrade pip \
    && pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

# Bake the embedding + reranker models into the image so the first request (and
# every restart) doesn't depend on downloading them. Non-fatal: the app falls
# back to downloading at start-up if this step cannot reach Hugging Face.
ARG EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
ARG RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('${EMBEDDING_MODEL}'); CrossEncoder('${RERANKER_MODEL}')" \
    || echo "WARNING: could not pre-download models (they will be fetched at start-up)"

COPY . .

# Run as an unprivileged user.
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/uploads /app/vector_db \
    && chown -R app:app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8000'), timeout=4)"

CMD ["sh", "scripts/start.sh"]
