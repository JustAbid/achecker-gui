# syntax=docker/dockerfile:1
FROM python:3.8-slim

ENV PYTHONUNBUFFERED=1

# Build dependencies for the analysis engine (pysha3, lxml, ...).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libxml2-dev libxslt1-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Everything `pip install -e .` needs, copied before the install for layer caching.
COPY setup.py README.md requirements.txt requirements-web.txt ./
COPY bin/ ./bin/
COPY src/ ./src/
COPY achecker_gui/ ./achecker_gui/

RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

# Optional: a solc build for analysing Solidity source with the CLI.
# The web UI only uses bytecode mode, which does not need solc.
RUN solc-select install 0.8.19 && solc-select use 0.8.19 || true

COPY samples/ ./samples/
RUN mkdir -p uploads

EXPOSE 5000
ENV MONGO_URI=mongodb://mongo:27017/

CMD ["gunicorn", "achecker_gui:create_app()", \
     "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "600"]
