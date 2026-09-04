# 🟢 THE SECURE BLACK BOX (Prop Firm Edition)
FROM rust:latest as builder

# Install Python & System Dependencies (Including OpenSSL, numpy, websockets)
RUN apt-get update && apt-get install -y python3 python3-pip pkg-config libssl-dev
RUN pip3 install --break-system-packages requests websocket-client fastapi uvicorn nltk numpy websockets

# Security: Non-root unprivileged appuser (UID 8888) - True Ghost Mode
RUN groupadd -g 8888 appuser && \
    useradd -u 8888 -g appuser -m -s /bin/bash appuser

WORKDIR /quant_engine
COPY . .
RUN chown -R appuser:appuser /quant_engine

# Compile Rust Engine to an impenetrable Binary
RUN cargo build --release --bin quant_engine

USER appuser

# Start the Master Execution Script
CMD ["/bin/bash", "./start.sh"]