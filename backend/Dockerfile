FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The build context is the repository root. Keep the application source and
# the reference ledgers together so Render has the same required CSVs as local
# Docker, without depending on a development-only bind mount.
COPY backend/app ./app
COPY data/synthetic ./data/synthetic

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
