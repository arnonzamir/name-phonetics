# Python sidecar service. espeak-ng is a system dep; the 307 MB phonikud
# model downloads on first run into HF cache (mount a volume to persist it).
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends espeak-ng \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY engine ./engine
COPY enrich ./enrich
COPY match ./match
COPY es ./es
COPY data ./data
COPY service ./service
COPY cli.py cluster.py ./

# editable install keeps /app the import root so enrich/../data resolves
RUN pip install --no-cache-dir -e ".[service]"

# Persist the downloaded model across restarts:  -v phonikud-cache:/root/.cache
ENV HF_HOME=/root/.cache/huggingface
EXPOSE 8099
CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8099"]
