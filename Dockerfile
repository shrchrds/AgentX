FROM python:3.13-slim

WORKDIR /app

# Copy dependency definition and metadata needed for packaging
COPY pyproject.toml README.md ./

# Install production dependencies
RUN pip install --no-cache-dir .

# Copy application source code
COPY app/ app/

EXPOSE 8000

# Health check to ensure service readiness
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

