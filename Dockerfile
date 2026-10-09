FROM python:3.11-slim

# Install system compilation packages needed for Open Quantum Safe
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone and compile liboqs
WORKDIR /opt
RUN git clone --branch main https://github.com \
    && cmake -S liboqs -B liboqs/build -DBUILD_SHARED_LIBS=ON \
    && cmake --build liboqs/build --parallel 4 \
    && cmake --install liboqs/build

# Set up the working directory inside the container
WORKDIR /app

# Copy requirement parameters and install them
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Force install the open-quantum-safe python wrapper package
RUN pip install --no-cache-dir pyoqs || pip install --no-cache-dir oqs

# Copy your actual project source files
COPY . .

# Expose network accessibility layout
ENV PYTHONPATH=/app
EXPOSE 10000

# Fire up your server application stack
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
