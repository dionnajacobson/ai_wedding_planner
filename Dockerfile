FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV LOG_FORMAT=json
ENV LOG_LEVEL=INFO

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
