import os
import sys
import json
import time
import socket
import asyncio
from typing import Tuple

# Load from .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ==========================================
# 🛡️ CREDENTIAL CONFIGURATION (GHOST-MODE)
# ==========================================
# API_ID and API_HASH should be placed inside a .env file:
# TELEGRAM_API_ID=12345678
# TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
API_ID = os.getenv("TELEGRAM_API_ID", "").strip()
API_HASH = os.getenv("TELEGRAM_API_HASH", "").strip()

# Target Telegram Channels to Monitor for Breaking Crypto Alpha
TARGET_CHANNELS = [
    "TreeNewsFeed",           # Institutional lightning fast news
    "binance_announcements",  # Binance listing/delisting alerts
    "tier10k",                # Up-to-the-second financial news
    "cointelegraph",          # Major crypto headlines
]

# UDP Destination (Rust Master Aggregator Engine)
RUST_UDP_HOST = "127.0.0.1"
RUST_UDP_PORT = 5000

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def broadcast_signal_to_rust(headline: str, sentiment_score: float, source: str = "TELEGRAM_SNIPER"):
    """Transmits high-priority sentiment payload to Rust Core via 0.01ms UDP socket."""
    payload = {
        "source": source,
        "timestamp": time.time(),
        "headline": headline[:100],  # Keep packet compact
        "sentiment_score": round(sentiment_score, 2)
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        udp_sock.sendto(data, (RUST_UDP_HOST, RUST_UDP_PORT))
        print(f"⚡ [NLP SENT TO RUST] Score: {sentiment_score:+.2f} | Headline: {headline[:60]}...", flush=True)
    except Exception as e:
        print(f"⚠️ [UDP ERROR] Could not reach Rust engine: {e}", flush=True)

# ==========================================
# 🧠 INSTITUTIONAL NLP SCORING ENGINE
# ==========================================
BULLISH_TRIGGERS = {
    "listing": 0.85,
    "listed": 0.80,
    "approved": 0.85,
    "sec approves": 0.95,
    "etf approved": 0.95,
    "partnership": 0.70,
    "investment": 0.65,
    "invested": 0.65,
    "acquisition": 0.75,
    "acquired": 0.75,
    "integration": 0.60,
    "mainnet launch": 0.75,
    "upgrade": 0.55,
    "surge": 0.50,
    "expansion": 0.55,
    "collaboration": 0.60,
}

BEARISH_TRIGGERS = {
    "hack": -0.90,
    "hacked": -0.95,
    "exploit": -0.90,
    "exploited": -0.90,
    "stolen": -0.85,
    "banned": -0.85,
    "delist": -0.85,
    "delisting": -0.90,
    "lawsuit": -0.80,
    "sued": -0.80,
    "investigation": -0.65,
    "bankruptcy": -0.95,
    "insolvent": -0.95,
    "halted": -0.70,
    "paused": -0.60,
    "vulnerability": -0.65,
}

def analyze_sentiment(text: str) -> Tuple[float, str]:
    """Analyzes raw headline text and outputs sentiment score [-1.0 to +1.0] and matched reason."""
    cleaned = text.lower()
    bullish_hits = [k for k in BULLISH_TRIGGERS if k in cleaned]
    bearish_hits = [k for k in BEARISH_TRIGGERS if k in cleaned]

    if bullish_hits and not bearish_hits:
        highest_weight = max(BULLISH_TRIGGERS[k] for k in bullish_hits)
        return highest_weight, f"BULLISH: {', '.join(bullish_hits)}"
    elif bearish_hits and not bullish_hits:
        lowest_weight = min(BEARISH_TRIGGERS[k] for k in bearish_hits)
        return lowest_weight, f"BEARISH: {', '.join(bearish_hits)}"
    elif bullish_hits and bearish_hits:
        # Conflicting signals -> Neutral defense
        return 0.0, "CONFLICTING_SIGNALS"
    
    return 0.0, "NEUTRAL"

# ==========================================
# 🚀 TELETHON LIVE STREAM WORKER
# ==========================================
async def start_telethon_listener():
    try:
        from telethon import TelegramClient, events
    except ImportError:
        print("⚠️ [DEPENDENCY MISSING] Telethon not installed. Run: pip install telethon python-dotenv", flush=True)
        print("⏳ Running NLP Sniper in Standby Heartbeat Mode...", flush=True)
        while True:
            await asyncio.sleep(60)

    if not API_ID or not API_HASH:
        print("⚠️ [CONFIGURATION NOTICE] TELEGRAM_API_ID or TELEGRAM_API_HASH is missing in .env file.", flush=True)
        print("💡 Place them in .env safely. Standby mode active...", flush=True)
        while True:
            await asyncio.sleep(60)

    print("🛡️ [TELETHON INITIALIZING] Connecting to Telegram Secure MTProto Gateway...", flush=True)
    session_name = "nlp_sniper_session"
    client = TelegramClient(session_name, int(API_ID), API_HASH)

    @client.on(events.NewMessage(chats=TARGET_CHANNELS))
    async def incoming_news_handler(event):
        text = event.raw_text
        if not text:
            return
        
        score, reason = analyze_sentiment(text)
        print(f"\n📰 [INCOMING NEWS] {time.strftime('%X')}: {text[:70]}...", flush=True)
        print(f"📊 [ANALYSIS] Score: {score:+.2f} | Reason: {reason}", flush=True)

        if score >= 0.5 or score <= -0.5:
            broadcast_signal_to_rust(text, score, source="TELEGRAM_LIVE_SNIPER")

    await client.start()
    print("✅ [NLP SNIPER ACTIVE] Listening 24/7 to breaking crypto alpha channels!", flush=True)
    await client.run_until_disconnected()

if __name__ == "__main__":
    print("====================================================")
    print("🎯 HALAL NLP SENTIMENT SNIPER (BOT 2) INITIALIZED")
    print("📡 Targets: Institutional Alpha & Announcement Feeds")
    print("🔒 Zero Data Leakage | Local UDP Bus -> Rust Core")
    print("====================================================")
    asyncio.run(start_telethon_listener())
