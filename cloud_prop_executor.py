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

# Environment Variables configured in Render Cloud Dashboard
PROP_FIRM_PROVIDER = os.getenv("PROP_FIRM_PROVIDER", "META_API") # Options: META_API, CTRADER, MATCH_TRADER, MOCK_TEST
PROP_ACCOUNT_ID = os.getenv("PROP_ACCOUNT_ID", "YOUR_PROP_ACCOUNT_ID")
META_API_TOKEN = os.getenv("META_API_TOKEN", "YOUR_META_API_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8663900968:AAGzLRKBoe8Hb72GVQctI8z9KVwaWLQMoes")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1432812458")

def notify_telegram(message: str):
    """Sends confirmation to user's phone via Telegram."""
    if not TELEGRAM_BOT_TOKEN:
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
        logging.info(f"🚀 [CLOUD EXECUTOR INITIALIZED] Provider: {self.provider} | Target Account: {self.account_id}")

    async def execute_cloud_order(self, symbol: str, action: str, volume: float, price: float, tp: float, sl: float) -> Dict[str, Any]:
        """
        Submits market order to prop firm directly from Render Cloud.
        """
        logging.info(f"⚡ [CLOUD AUTO-TRADE] Initiating {action} for {symbol} | Volume: {volume} | Target TP: {tp}")

        # If MetaAPI is configured (Connects Render directly to MT5 account in cloud)
        if self.provider == "META_API" and META_API_TOKEN != "YOUR_META_API_TOKEN":
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
        """
        class UdpProtocol(asyncio.DatagramProtocol):
            def __init__(self, executor):
                self.executor = executor

            def datagram_received(self, data, addr):
                try:
                    payload = json.loads(data.decode())
                    logging.info(f"📩 [SIGNAL RECEIVED FROM RUST CORE] {payload}")
                    action = payload.get("action", "BUY")
                    symbol = payload.get("symbol", "ETHUSD")
                    price = payload.get("price", 2500.0)
                    tp_pct = payload.get("tp_pct", 0.0035)
                    sl_pct = payload.get("sl_pct", 0.0030)
                    
                    tp = price * (1.0 + tp_pct)
                    sl = price * (1.0 - sl_pct)
                    
                    asyncio.create_task(self.executor.execute_cloud_order(
                        symbol=symbol,
                        action=action,
                        volume=0.1,  # Calculated micro-lot
                        price=price,
                        tp=tp,
                        sl=sl
                    ))
                except Exception as e:
                    logging.error(f"Error decoding UDP packet: {e}")

        loop = asyncio.get_running_loop()
        logging.info("🎧 Cloud Prop Executor listening on 127.0.0.1:5002 for Rust signals...")
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
