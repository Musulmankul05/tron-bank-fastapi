FROM python:3.14-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . .

ENV UV_NO_DEV=1
RUN uv sync --locked
CMD ["uv", "run", "uvicorn", "main:app"]