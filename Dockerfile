# The public demo on Render (see render.yaml). At home, use `make setup` and `make run` instead:
# this image runs the same app with EBYAFAAYO_DEMO=1 (sample data, a banner, no deleting).

FROM node:24-slim AS web
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ARG OLLAMA_VERSION=0.40.13
ARG TEMPORAL_VERSION=1.9.1
# Set to 0 to build without Ollama (for a quick local test of the rest)
ARG WITH_OLLAMA=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg curl ca-certificates zstd \
 && rm -rf /var/lib/apt/lists/*

# Ollama for Gemma 4. Render has no GPU, so the GPU libraries (most of the 1.5 GB) are removed.
RUN if [ "$WITH_OLLAMA" = 1 ]; then \
      curl -fsSL "https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/ollama-linux-amd64.tar.zst" \
        | tar --zstd -x -C /usr/local \
      && find /usr/local/lib/ollama -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + \
      && ollama --version; \
    fi

# The Temporal CLI, which includes the dev server
RUN curl -fsSL "https://temporal.download/cli/archive/v${TEMPORAL_VERSION}?platform=linux&arch=amd64" \
      | tar -xz -C /usr/local/bin temporal \
 && temporal --version

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY scripts/start-render.sh scripts/start-render.sh
COPY --from=web /app/frontend/dist frontend/dist

ENV EBYAFAAYO_DEMO=1 \
    EBYAFAAYO_DATA=/data/app \
    EBYAFAAYO_GEMMA=gemma4:e2b \
    OLLAMA_MODELS=/data/ollama \
    PYTHONUNBUFFERED=1
CMD ["bash", "scripts/start-render.sh"]
