
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    ninja-build \
    build-essential \
    git \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone --depth 1 --branch main \
    https://github.com/open-quantum-safe/liboqs.git /tmp/liboqs && \
    cmake -S /tmp/liboqs -B /tmp/liboqs/build \
    -GNinja \
    -DBUILD_SHARED_LIBS=ON \
    -DOQS_MINIMAL_BUILD="SIG_ml_dsa_65" \
    -DCMAKE_BUILD_TYPE=Release && \
    cmake --build /tmp/liboqs/build --parallel 2 && \
    cmake --install /tmp/liboqs/build && \
    ldconfig && \
    rm -rf /tmp/liboqs

COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY . /app

EXPOSE 10000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
