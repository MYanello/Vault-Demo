FROM ghcr.io/astral-sh/uv:debian

USER root

WORKDIR /app

COPY . .

RUN uv sync

CMD [ "uv", "run", "python", "/app/jwks.py"]