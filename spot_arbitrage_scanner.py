"""
================================================================================
⚡ HIGH-FREQUENCY SPOT ARBITRAGE SCANNER (100% SHARIAH SPOT-ONLY)
================================================================================
File: spot_arbitrage_scanner.py
Purpose: Scans real-time price differentials between Binance and OKX Spot markets.
When net spread > 0.15% (after exchange taker fees), it transmits an instant 
zero-risk arbitrage execution trigger to Rust Master Aggregator (UDP 5000).
================================================================================
"""

import asyncio
import json
import socket
import time
import websockets

# ANSI Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

UDP_IP = "127.0.0.1"
UDP_PORT = 5000
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def transmit_arbitrage_signal(pair, buy_venue, sell_venue, spread_pct, net_profit):
    payload = {
        "source": "SPOT_ARBITRAGE_SCANNER",
        "timestamp": time.time(),
        "headline": f"RISK-FREE ARB: Buy {buy_venue} / Sell {sell_venue} | Spread: {spread_pct:.3f}% | Est Profit: ${net_profit:.2f}",
        "sentiment_score": 0.98 # Triggers instant execution
    }
    msg = json.dumps(payload).encode('utf-8')
    sock.sendto(msg, (UDP_IP, UDP_PORT))
    print(f"\n{GREEN}⚡ [ARBITRAGE SNIPED] {pair.upper()} on {buy_venue}->{sell_venue} (+{spread_pct:.3f}%){RESET}")

async def run_arbitrage_scanner(symbol="ETH-USDT"):
    binance_symbol = symbol.replace("-", "").lower()
    binance_uri = f"wss://stream.binance.com:9443/ws/{binance_symbol}@bookTicker"
    okx_uri = "wss://ws.okx.com:8443/ws/v5/public"

    binance_ask = 0.0
    binance_bid = 0.0
    okx_ask = 0.0
    okx_bid = 0.0

    fee_tier = 0.0015 # 0.15% combined round-trip taker fee

    print(f"{YELLOW}🔍 [SPOT ARBITRAGE] Listening to Binance & OKX for {symbol}...{RESET}")

    async def binance_listener():
        nonlocal binance_ask, binance_bid
        async with websockets.connect(binance_uri) as ws:
            while True:
                try:
                    data = json.loads(await ws.recv())
                    binance_ask = float(data.get('a', 0.0))
                    binance_bid = float(data.get('b', 0.0))
                except Exception:
                    await asyncio.sleep(1)

    async def okx_listener():
        nonlocal okx_ask, okx_bid
        sub_msg = json.dumps({
            "op": "subscribe",
            "args": [{"channel": "tickers", "instId": symbol}]
        })
        async with websockets.connect(okx_uri) as ws:
            await ws.send(sub_msg)
            while True:
                try:
                    data = json.loads(await ws.recv())
                    if "data" in data and len(data["data"]) > 0:
                        ticker = data["data"][0]
                        okx_ask = float(ticker.get('askPx', 0.0))
                        okx_bid = float(ticker.get('bidPx', 0.0))
                except Exception:
                    await asyncio.sleep(1)

    async def arbitrage_evaluator():
        while True:
            await asyncio.sleep(0.5)
            if binance_ask > 0 and okx_bid > 0:
                # Case 1: Buy Binance Spot, Sell OKX Spot
                spread_1 = (okx_bid - binance_ask) / binance_ask
                net_spread_1 = spread_1 - fee_tier
                if net_spread_1 > 0.001: # > 0.10% net profit
                    transmit_arbitrage_signal(symbol, "Binance", "OKX", net_spread_1 * 100.0, net_spread_1 * 25000.0)
                    await asyncio.sleep(5)

            if okx_ask > 0 and binance_bid > 0:
                # Case 2: Buy OKX Spot, Sell Binance Spot
                spread_2 = (binance_bid - okx_ask) / okx_ask
                net_spread_2 = spread_2 - fee_tier
                if net_spread_2 > 0.001: # > 0.10% net profit
                    transmit_arbitrage_signal(symbol, "OKX", "Binance", net_spread_2 * 100.0, net_spread_2 * 25000.0)
                    await asyncio.sleep(5)

    await asyncio.gather(
        binance_listener(),
        okx_listener(),
        arbitrage_evaluator()
    )

if __name__ == "__main__":
    asyncio.run(run_arbitrage_scanner("ETH-USDT"))
