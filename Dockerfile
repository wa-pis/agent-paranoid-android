# syntax=docker/dockerfile:1.7

ARG PYTHON_IMAGE=python:3.12-slim-bookworm@sha256:d50fb7611f86d04a3b0471b46d7557818d88983fc3136726336b2a4c657aa30b
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.11.23@sha256:d0a0a753ab981624b49c97abc98821c1c09f4ca69d1ef5cee69c501be3d88479

FROM ${UV_IMAGE} AS uv

FROM ${PYTHON_IMAGE} AS build-base

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY --from=uv /uv /uvx /usr/local/bin/
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src

FROM build-base AS cli-builder
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --no-group docs

FROM build-base AS generator-builder
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --no-group docs --extra mcp

FROM build-base AS trino-builder
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --no-group docs --extra mcp --extra trino

FROM ${PYTHON_IMAGE} AS runtime-base

ARG APP_VERSION=0.8.1
ARG VCS_REF=unknown
ARG SOURCE_URL=https://github.com/wa-pis/agent-paranoid-android

LABEL org.opencontainers.image.title="Agent Paranoid Android" \
      org.opencontainers.image.description="Safety-first synthetic test data generation agent" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="${SOURCE_URL}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${APP_VERSION}"

ENV HOME=/home/agent \
    PATH=/app/.venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid 65532 agent \
    && useradd --no-log-init --uid 65532 --gid 65532 \
        --home-dir /home/agent --create-home --shell /usr/sbin/nologin agent \
    && install -d -o 65532 -g 65532 -m 0700 /workspace /audit

WORKDIR /workspace
USER 65532:65532
STOPSIGNAL SIGTERM

FROM runtime-base AS cli
COPY --from=cli-builder --chown=65532:65532 /app/.venv /app/.venv
ENV TEST_DATA_AGENT_CONTAINER_TARGET=cli
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD ["python", "-m", "test_data_agent.container_health", "cli"]
ENTRYPOINT ["test-data-agent"]

FROM runtime-base AS generator-mcp
COPY --from=generator-builder --chown=65532:65532 /app/.venv /app/.venv
ENV TEST_DATA_AGENT_CONTAINER_TARGET=generator-mcp \
    TEST_DATA_AGENT_WORKSPACE_ROOT=/workspace
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD ["python", "-m", "test_data_agent.container_health", "generator-mcp"]
ENTRYPOINT ["test-data-agent-mcp-generator"]

FROM runtime-base AS trino-mcp
COPY --from=trino-builder --chown=65532:65532 /app/.venv /app/.venv
ENV TEST_DATA_AGENT_CONTAINER_TARGET=trino-mcp
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD ["python", "-m", "test_data_agent.container_health", "trino-mcp"]
ENTRYPOINT ["test-data-agent-mcp-trino"]
