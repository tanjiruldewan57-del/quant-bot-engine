# 🟢 THE SECURE BLACK BOX (Prop Firm Edition)
FROM rust:1.80-slim as builder

# Install Python & Dependencies
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install --break-system-packages requests websocket-client fastapi uvicorn nltk

WORKDIR /quant_engine
COPY . .

# Compile Rust Engine to an impenetrable Binary
RUN cargo build --release --bin quant_engine

# Start the Master Execution Script
CMD ["/bin/bash", "./start.sh"]