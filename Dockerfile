# CreditSentinel image — API and MLflow server run from this image.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Install dependencies first (cached until lockfile changes).
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Install the project.
COPY src ./src
COPY policies ./policies
RUN uv sync --frozen --no-dev

# Bake a governed model into the image. Without this a
# cold container spends time training before it can answer.
# Deterministic: same pinned seed, same artefacts.
RUN mkdir -p /app/data /app/mlflow \
 && creditsentinel-train

COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
