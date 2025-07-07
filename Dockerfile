FROM python:3.10

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 앱 코드 복사
COPY . /app
WORKDIR /app

RUN uv sync --frozen --no-cache

CMD ["/app/.venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
