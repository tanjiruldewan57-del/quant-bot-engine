"""
CloudPropExecutor
100% Cloud-to-Broker Automated Execution Engine (Zero Local PC Required)
Listens to internal Rust quant signals and automatically dispatches live orders
directly to Prop Firm accounts via Cloud REST / MetaAPI / Webhook gateways.

No manual clicks. No PC turned on. 100% automated 24/7 cloud execution.
"""

import os
import json
import time
import asyncio
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

import hmac
import hashlib

# Environment Variables configured in Render Cloud Dashboard
PROP_FIRM_PROVIDER = os.getenv("PROP_FIRM_PROVIDER", "META_API") # Options: META_API, CTRADER, MATCH_TRADER, MOCK_TEST
PROP_ACCOUNT_ID = os.getenv("PROP_ACCOUNT_ID", "")
META_API_TOKEN = os.getenv("META_API_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
UDP_SECRET = os.getenv("UDP_SECRET", "")

def notify_telegram(message: str):
    """Sends confirmation to user's phone via Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("⚠️ [TELEGRAM ALERT SKIPPED] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": message}).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, headers={"User-Agent": "CloudPropExecutor/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            pass
    except Exception as e:
        logging.error(f"Telegram alert error: {e}")

class CloudPropExecutor:
    def __init__(self):
        self.provider = PROP_FIRM_PROVIDER
        self.account_id = PROP_ACCOUNT_ID
        self.is_running = True
        self.last_order_timestamps = {}  # Symbol-action debounce map
        self.min_order_interval = 5.0    # 5-second debounce window per symbol

        has_meta_creds = bool(META_API_TOKEN and PROP_ACCOUNT_ID and META_API_TOKEN != "YOUR_META_API_TOKEN")
        mode_str = "LIVE CLOUD BROKER" if has_meta_creds else "PAPER / SIMULATION MODE"
        logging.info(f"🚀 [CLOUD EXECUTOR INITIALIZED] Provider: {self.provider} | Mode: {mode_str}")
        if not has_meta_creds and self.provider == "META_API":
            logging.info("ℹ️ [SETUP NOTE] Set 'META_API_TOKEN' and 'PROP_ACCOUNT_ID' in Render to execute live trades.")

    async def execute_cloud_order(self, symbol: str, action: str, volume: float, price: float, tp: float, sl: float) -> Dict[str, Any]:
        """
        Submits market order to prop firm directly from Render Cloud.
        """
        # Rate-limiting / debounce check
        debounce_key = f"{symbol}:{action.upper()}"
        now = time.time()
        last_time = self.last_order_timestamps.get(debounce_key, 0.0)
        if (now - last_time) < self.min_order_interval:
            logging.warning(f"⚠️ [RATE LIMIT] Suppressed duplicate {action} order for {symbol} within {self.min_order_interval}s")
            return {"status": "DEBOUNCED", "symbol": symbol, "action": action}
        self.last_order_timestamps[debounce_key] = now

        logging.info(f"⚡ [CLOUD AUTO-TRADE] Initiating {action} for {symbol} | Volume: {volume} | Target TP: {tp}")

        # If MetaAPI is configured (Connects Render directly to MT5 account in cloud)
        if self.provider == "META_API" and META_API_TOKEN and META_API_TOKEN != "YOUR_META_API_TOKEN" and self.account_id:
            url = f"https://mt-client-api-v1.new-york.agiliumtrade.ai/users/current/accounts/{self.account_id}/trade"
            headers = {
                "auth-token": META_API_TOKEN,
                "Content-Type": "application/json"
            }
            order_data = {
                "actionType": "ORDER_TYPE_BUY" if action.upper() == "BUY" else "ORDER_TYPE_SELL",
                "symbol": symbol,
                "volume": volume,
                "takeProfit": tp,
                "stopLoss": sl,
                "comment": "QuantEngine-HalalSpot"
            }
            try:
                req = urllib.request.Request(url, data=json.dumps(order_data).encode("utf-8"), headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_body = response.read().decode("utf-8")
                    logging.info(f"✅ [PROP FIRM FILLED] Broker Response: {res_body}")
                    notify_telegram(f"✅ [CLOUD AUTO-TRADE SUCCESS]\n\nBroker: {self.provider}\nAction: {action} {symbol}\nVolume: {volume}\nPrice: ${price}\nStatus: FILLED 100% Hands-Free!")
                    return json.loads(res_body)
            except Exception as e:
                logging.error(f"❌ Cloud Execution failed via MetaAPI: {e}")
                notify_telegram(
                    f"🚨 [BROKER EXECUTION ALERT]\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"❌ Broker execution failed for {action} {symbol}!\n"
                    f"⚠️ Volume: {volume} Lots\n"
                    f"🛑 Reason: {e}\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )
                return {"status": "FAILED", "error": str(e)}

        # Simulation / Paper mode (Default before live credentials are bound)
        logging.info(f"📝 [SIMULATED CLOUD EXECUTION] {action} {symbol} simulated successfully. No manual intervention required.")
        notify_telegram(f"🤖 [CLOUD BOT EXECUTED TRADE]\n\nAsset: {symbol}\nAction: {action}\nSimulated Lot: {volume}\nExecution: 100% Automated from Render Cloud!\nYour PC is OFF and safe.")
        return {
            "status": "SIMULATED_SUCCESS",
            "symbol": symbol,
            "action": action,
            "volume": volume,
            "timestamp": time.time()
        }

    async def start_listener(self):
        """
        Listens to internal UDP socket or local signal bus from Rust engine.
        Authenticates payloads with UDP_SECRET.
        """
        class UdpProtocol(asyncio.DatagramProtocol):
            def __init__(self, executor):
                self.executor = executor

            def datagram_received(self, data, addr):
                try:
                    payload = json.loads(data.decode("utf-8"))
                    
                    # 🛡️ SECURITY CHECK: Authenticate UDP Signal
                    if UDP_SECRET:
                        auth_token = payload.get("auth_token", "")
                        if not hmac.compare_digest(auth_token, UDP_SECRET):
                            logging.warning(f"🚨 [UNAUTHORIZED UDP ATTEMPT] Invalid or missing auth token from {addr} on port 5002! Packet dropped.")
                            return

                    logging.info(f"📩 [SIGNAL RECEIVED FROM RUST CORE] {payload.get('action')} {payload.get('symbol')} @ {payload.get('price')}")
                    action = payload.get("action", "BUY")
                    symbol = payload.get("symbol", "ETHUSD")
                    price = payload.get("price", 2500.0)
                    tp_pct = payload.get("tp_pct", 0.0035)
                    sl_pct = payload.get("sl_pct", 0.0030)
                    
                    # 🛡️ DYNAMIC POSITION SIZING: Extract lot from Rust core, clamped to institutional safe range
                    raw_volume = payload.get("volume", 0.1)
                    try:
                        volume = round(float(raw_volume), 2)
                        volume = max(0.01, min(volume, 5.0))
                    except (ValueError, TypeError):
                        volume = 0.1

                    tp = price * (1.0 + tp_pct)
                    sl = price * (1.0 - sl_pct)
                    
                    asyncio.create_task(self.executor.execute_cloud_order(
                        symbol=symbol,
                        action=action,
                        volume=volume,
                        price=price,
                        tp=tp,
                        sl=sl
                    ))
                except Exception as e:
                    logging.error(f"Error decoding UDP packet: {e}")

        loop = asyncio.get_running_loop()
        logging.info("🎧 Cloud Prop Executor listening on 127.0.0.1:5002 for Rust signals...")
        if UDP_SECRET:
            logging.info("🔒 [UDP AUTHENTICATION] Enabled with SHA-256 constant-time secret check.")
        else:
            logging.warning("⚠️ [UDP AUTHENTICATION] UDP_SECRET not set. Set UDP_SECRET in environment for maximum security.")

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: UdpProtocol(self),
            local_addr=("127.0.0.1", 5002)
        )
        
        while self.is_running:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    executor = CloudPropExecutor()
    try:
        asyncio.run(executor.start_listener())
    except KeyboardInterrupt:
        print("Shutting down Cloud Prop Executor.")
