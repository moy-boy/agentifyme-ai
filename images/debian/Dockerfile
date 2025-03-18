FROM debian:bookworm-slim

LABEL maintainer="AgentifyMe Devs <devs@agentifyme.ai>"
LABEL description="AgentifyMe docker image for python runtime"
LABEL org.opencontainers.image.source="https://github.com/agentifyme/agentifyme-py"
LABEL version=0.2

ARG PYTHON_VERSION=3.13
ARG AGENTIFYME_VERSION=0.2

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    pkg-config \
    curl \
    openssl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN useradd -m -s /bin/bash agnt5

# Set working directory
WORKDIR /home/agnt5/app
RUN chown agnt5:agnt5 /home/agnt5/app

USER agnt5

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="${PATH}:/home/agnt5/.local/bin:/home/agnt5/.venv/bin:/home/agnt5/.agentifyme/bin"

RUN uv venv --python ${PYTHON_VERSION} ${HOME}/.venv

RUN uv pip install --upgrade pip && \
    uv pip install agentifyme~=${AGENTIFYME_VERSION}

