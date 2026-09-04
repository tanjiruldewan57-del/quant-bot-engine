# 🟢 THE SECURE BLACK BOX (Prop Firm Edition)
FROM rust:1.80-slim as builder

# Install Python & Dependencies (Including numpy and websockets for Extreme Mode)
RUN apt-get update && apt-get install -y python3 python3-pip
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