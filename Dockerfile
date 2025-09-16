# Dockerfile
# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-alpine

# Install the project into `/app`
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Runtime libs
RUN apk add --no-cache libstdc++ libffi openssl git
RUN apk add --no-cache --virtual .build-deps \
    build-base python3-dev libffi-dev openssl-dev \
    linux-headers rust cargo ripgrep

COPY . /app
RUN  uv sync --no-dev
RUN apk del .build-deps && rm -rf /root/.cache/uv

ENV PATH="/app/.venv/bin:$PATH"
ENV WORKSPACE_DIR="/workspace"

ENTRYPOINT []

CMD ["python", "-m", "mle_kit_mcp"]
