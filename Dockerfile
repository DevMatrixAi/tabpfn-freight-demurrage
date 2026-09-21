# Freight demurrage desk preview — mock-first (no TABPFN_TOKEN required).
# Demo login: demo / demurrage
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8765 \
    DESK_DEMO_USER=demo \
    DESK_DEMO_PASSWORD=demurrage

COPY requirements.txt pyproject.toml README.md ./
COPY src ./src
COPY apps ./apps
COPY domains ./domains
COPY fixtures ./fixtures
COPY examples ./examples
COPY app.py ./

RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir -e .

EXPOSE 8765
CMD ["sh", "-c", "uvicorn apps.desk.app:app --host 0.0.0.0 --port ${PORT:-8765}"]
