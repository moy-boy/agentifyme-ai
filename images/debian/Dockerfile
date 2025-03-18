FROM debian:bookworm-slim

ARG PYTHON_VERSION=3.13
ARG AGENTIFYME_VERSION=0.2
ARG AGENTIFYME_INIT_VERSION=0.1
LABEL maintainer="AgentifyMe Devs <devs@agentifyme.ai>"
LABEL description="AgentifyMe docker image for python runtime"
LABEL version=${AGENTIFYME_VERSION}-py${PYTHON_VERSION}

LABEL org.opencontainers.image.source="https://github.com/agentifyme/agentifyme-py"
LABEL org.opencontainers.image.url="https://agentifyme.ai"
LABEL org.opencontainers.image.created=${BUILD_DATE}
LABEL org.opencontainers.image.authors="AgentifyMe Devs <devs@agentifyme.ai>"
LABEL org.opencontainers.image.version=${AGENTIFYME_VERSION}-py${PYTHON_VERSION}
LABEL org.opencontainers.image.title="AgentifyMe Python Runtime"
LABEL org.opencontainers.image.description="AgentifyMe docker image for python runtime"

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

# Get the architecture using uname
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then \
        ARCH_NAME="arm64"; \
    elif [ "$ARCH" = "x86_64" ]; then \
        ARCH_NAME="x86_64"; \
    else \
        echo "Unsupported architecture: $ARCH"; \
        exit 1; \
    fi && \
    curl -L https://storage.botifyme.dev/supervisor/supervisor-linux-${ARCH_NAME}-${AGENTIFYME_INIT_VERSION}-py${PYTHON_VERSION} -o /home/agnt5/.local/bin/agnt5-init && \
    chmod +x /home/agnt5/.local/bin/agnt5-init

ENV PATH="${PATH}:/home/agnt5/.local/bin:/home/agnt5/.venv/bin"

RUN uv venv --python ${PYTHON_VERSION} ${HOME}/.venv

RUN uv pip install --upgrade pip && \
    uv pip install agentifyme~=${AGENTIFYME_VERSION}

ENTRYPOINT ["agnt5-init"]

