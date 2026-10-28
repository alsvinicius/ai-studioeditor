FROM node:22-bookworm-slim@sha256:de170b39439eb0e5a3444ad7d60b015614a381e10fecae2e30ec9e735122f38d AS node-runtime

FROM python:3.12-slim@sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f

COPY --from=node-runtime /usr/local/ /usr/local/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/models/huggingface \
    XDG_CACHE_HOME=/models/cache \
    PATH="/app/node_modules/.bin:/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg ca-certificates libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv==0.8.22 \
    && uv sync --locked --no-dev --no-install-project
COPY LICENSE THIRD_PARTY_NOTICES.md ./
COPY docs/reference/python-licenses.md docs/reference/npm-licenses.md docs/reference/container-debian-packages.txt /app/docs/reference/
COPY app ./app
RUN mkdir -p /data /models

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
