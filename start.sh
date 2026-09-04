#!/bin/bash
echo "======================================================"
echo "🚀 [SYSTEM BOOT] Quant Engine Black Box Starting..."
echo "🛡️  Ghost Mode | Zero-Cost | Halal Certified"
echo "======================================================"

# 📁 Ensure log directory exists
mkdir -p logs

# 🌐 Start SaaS API & Health Check Endpoint (Render Port Binding)
echo "🌐 Starting SaaS API Health Check Endpoint on Port ${PORT:-8000}..."
python3 saas_api.py >> logs/saas_api.log 2>&1 &
SAAS_PID=$!
echo "  ✅ SaaS API PID: $SAAS_PID"
sleep 1

# ⚡ LOAD BALANCING: Start microservices with staggered delays
# to prevent all of them hitting UDP port 5000 simultaneously

echo "📡 [1/4] Starting NLP Sentiment Sniper..."
python3 nlp_sentiment_sniper.py >> logs/nlp_sniper.log 2>&1 &
NLP_PID=$!
echo "  ✅ NLP Sniper PID: $NLP_PID"
sleep 1

echo "📊 [2/4] Starting Extreme Mode Quant Engine..."
python3 extreme_mode_engine.py >> logs/extreme_mode.log 2>&1 &
EXTREME_PID=$!
echo "  ✅ Extreme Mode PID: $EXTREME_PID"
sleep 1

echo "🔍 [3/4] Starting Spot Arbitrage Scanner..."
python3 spot_arbitrage_scanner.py >> logs/arbitrage.log 2>&1 &
ARB_PID=$!
echo "  ✅ Arbitrage Scanner PID: $ARB_PID"
sleep 1

echo "🐳 [4/4] Starting Whale Tracker..."
python3 whale_tracker.py >> logs/whale_tracker.log 2>&1 &
WHALE_PID=$!
echo "  ✅ Whale Tracker PID: $WHALE_PID"

# Give all microservices 3 seconds to fully arm
echo ""
echo "⏳ Waiting 3s for microservices to arm..."
sleep 3

echo ""
echo "======================================================"
echo "🛡️  Starting Rust Master Execution Engine..."
echo "======================================================"

# 🔄 AUTO-RESTART LOOP for Rust Engine (EDGE CASE: Server crash recovery)
RUST_RESTART_COUNT=0
while true; do
    if [ -f "./target/release/quant_engine" ]; then
        ./target/release/quant_engine 2>&1 | tee -a logs/rust_engine.log
    else
        cargo run --release --bin quant_engine 2>&1 | tee -a logs/rust_engine.log
    fi

    EXIT_CODE=$?
    RUST_RESTART_COUNT=$((RUST_RESTART_COUNT + 1))
    echo ""
    echo "⚠️  [RESTART #$RUST_RESTART_COUNT] Rust engine exited with code $EXIT_CODE. Restarting in 5s..."
    echo "$(date): Engine restart #$RUST_RESTART_COUNT (exit code: $EXIT_CODE)" >> logs/restart_history.log

    # If circuit breaker triggered (clean exit), wait longer before restart
    if [ $EXIT_CODE -eq 0 ]; then
        echo "🛑 Circuit Breaker detected. Waiting 60s before restart..."
        sleep 60
    else
        sleep 5
    fi
done