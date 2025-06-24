ARG PYTHON_VERSION=3.13.1

# Builder

FROM python:${PYTHON_VERSION}-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml /app/
COPY README.md /app/

RUN python -m venv .venv

RUN uv sync --python .venv/bin/python --no-install-project --no-dev

COPY oblivionis /app/oblivionis

RUN .venv/bin/python -m pip install .

# Runtime

FROM python:${PYTHON_VERSION}-slim

COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH"

CMD ["/app/.venv/bin/oblivionis"]
