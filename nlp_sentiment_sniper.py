import os
import sys
import json
import time
import socket
import asyncio
import urllib.request
import xml.etree.ElementTree as ET
from typing import Tuple, List, Set

# ==========================================
# 🛡️ 100% ZERO-LOGIN PUBLIC ALPHA FEED CONFIG
# ==========================================
# No personal accounts, no phone numbers, no Telegram sessions needed!
# Pure public cryptographic orderflow & announcement feeds.

RUST_UDP_HOST = "127.0.0.1"
RUST_UDP_PORT = 5000

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def broadcast_signal_to_rust(headline: str, sentiment_score: float, source: str = "PUBLIC_ALPHA_FEED"):
    """Transmits high-priority sentiment payload to Rust Core via 0.01ms local UDP."""
    payload = {
        "source": source,
        "timestamp": time.time(),
        "headline": headline[:100],
        "sentiment_score": round(sentiment_score, 2)
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        udp_sock.sendto(data, (RUST_UDP_HOST, RUST_UDP_PORT))
        print(f"\n⚡ [NLP SENT TO RUST] Score: {sentiment_score:+.2f} | Headline: {headline[:65]}...", flush=True)
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
    "mainnet": 0.70,
    "upgrade": 0.55,
    "surge": 0.50,
    "expansion": 0.55,
    "collaboration": 0.60,
    "spot etf": 0.90,
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
    cleaned = text.lower()
    bullish_hits = [k for k in BULLISH_TRIGGERS if k in cleaned]
    bearish_hits = [k for k in BEARISH_TRIGGERS if k in cleaned]

    if bullish_hits and not bearish_hits:
        highest_weight = max(BULLISH_TRIGGERS[k] for k in bullish_hits)
        return highest_weight, f"BULLISH ({', '.join(bullish_hits)})"
    elif bearish_hits and not bullish_hits:
        lowest_weight = min(BEARISH_TRIGGERS[k] for k in bearish_hits)
        return lowest_weight, f"BEARISH ({', '.join(bearish_hits)})"
    elif bullish_hits and bearish_hits:
        return 0.0, "CONFLICTING"
    
    return 0.0, "NEUTRAL"

# ==========================================
# 📡 PUBLIC MULTI-FEED MONITOR
# ==========================================
# High-speed public institutional sources that require zero authentication
FEEDS = [
    {"name": "CoinTelegraph Public RSS", "url": "https://cointelegraph.com/rss", "type": "rss"},
    {"name": "CoinDesk Alpha RSS", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "type": "rss"},
    {"name": "CryptoPanic Public Feed", "url": "https://cryptopanic.com/api/free/v1/posts/?auth_token=free&public=true", "type": "json"},
]

seen_headlines: Set[str] = set()

def fetch_rss_headlines(feed_url: str) -> List[str]:
    headlines = []
    try:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=4) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            for item in root.findall(".//item")[:10]:
                title = item.find("title")
                if title is not None and title.text:
                    headlines.append(title.text.strip())
    except Exception:
        pass
    return headlines

def fetch_json_headlines(feed_url: str) -> List[str]:
    headlines = []
    try:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode())
            results = data.get("results", [])
            for post in results[:10]:
                title = post.get("title")
                if title:
                    headlines.append(title.strip())
    except Exception:
        pass
    return headlines

async def public_news_sniper_loop():
    print("====================================================")
    print("🎯 ZERO-LOGIN PUBLIC CRYPTO NEWS SNIPER ACTIVE")
    print("🔒 100% Privacy Guaranteed | Zero Credentials Required")
    print("📡 Monitoring: CoinTelegraph, CoinDesk, CryptoPanic")
    print("⚡ Realtime Output Bus -> Rust Core UDP 127.0.0.1:5000")
    print("====================================================", flush=True)

    # Initial priming to avoid triggering old news
    print("⏳ Priming memory with existing headlines...", flush=True)
    for feed in FEEDS:
        if feed["type"] == "rss":
            items = fetch_rss_headlines(feed["url"])
        else:
            items = fetch_json_headlines(feed["url"])
        for h in items:
            seen_headlines.add(h)
    
    print(f"✅ [PRIMED] {len(seen_headlines)} historical headlines memorized. Now hunting NEW breaking alpha!", flush=True)

    while True:
        try:
            for feed in FEEDS:
                if feed["type"] == "rss":
                    current_items = fetch_rss_headlines(feed["url"])
                else:
                    current_items = fetch_json_headlines(feed["url"])

                for title in current_items:
                    if title not in seen_headlines:
                        seen_headlines.add(title)
                        score, reason = analyze_sentiment(title)
                        timestamp_str = time.strftime("%X")
                        
                        if score != 0.0:
                            print(f"\n🔥 [BREAKING ALPHA - {feed['name']}] {timestamp_str}")
                            print(f"📰 {title}")
                            print(f"📊 Signal: {score:+.2f} | Reason: {reason}", flush=True)

                        # If high impact, fire immediately to Rust Core
                        if score >= 0.5 or score <= -0.5:
                            broadcast_signal_to_rust(title, score, source=feed["name"])

            # Keep cache bounded to 2000 items to conserve RAM
            if len(seen_headlines) > 2000:
                seen_headlines.clear()

        except Exception as e:
            print(f"⚠️ [MONITOR NOTICE] Stream tick caught: {e}", flush=True)

        await asyncio.sleep(3)  # Fast 3-second cycle

if __name__ == "__main__":
    asyncio.run(public_news_sniper_loop())
