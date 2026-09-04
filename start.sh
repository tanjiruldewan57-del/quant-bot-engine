#!/bin/bash
echo "🚀 [SYSTEM BOOT] Booting Quant Engine Black Box..."

# 1. Start the B2B SaaS API (Runs in background)
echo "🌐 Starting SaaS API on Port 8000..."
python3 saas_api.py &

# 2. Start the AI & On-Chain Microservices (Runs in background)
echo "🐳 Starting Whale Tracker Microservice..."
python3 whale_tracker.py &

python3 nlp_sentiment_sniper.py &
python3 extreme_mode_engine.py &
python3 spot_arbitrage_scanner.py &

# 3. Give the Microservices 2 seconds to warm up
sleep 2

# 4. Start the Rust Master Execution Engine (Runs in foreground to keep server alive)
echo "🛡️ Starting Rust Master Engine..."
if [ -f "./target/release/quant_engine" ]; then
    ./target/release/quant_engine
else
    cargo run --release --bin quant_engine
fi