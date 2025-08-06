FROM mcr.microsoft.com/devcontainers/python:3.12
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=caddy:2.9.1 /usr/bin/caddy /bin/
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /bin v3.41.0
USER vscode
COPY --chown=vscode:vscode .zshrc /home/vscode/.zshrc
ENV UV_PROJECT_ENVIRONMENT=/home/vscode/.venv
WORKDIR /home/vscode
