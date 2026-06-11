FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY README.md ./
COPY src/ src/
RUN pip install --no-cache-dir .
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
ENTRYPOINT ["nifi-mcp"]
