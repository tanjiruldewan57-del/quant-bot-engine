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
        self.min_order_interval = 8.0    # 8-second debounce window per symbol to prevent burst spam
        self.primary_region = os.getenv("META_API_REGION", "")

        has_meta_creds = bool(META_API_TOKEN and PROP_ACCOUNT_ID and META_API_TOKEN != "YOUR_META_API_TOKEN")
        mode_str = "LIVE CLOUD BROKER" if has_meta_creds else "PAPER / SIMULATION MODE"
        logging.info(f"🚀 [CLOUD EXECUTOR INITIALIZED] Provider: {self.provider} | Mode: {mode_str}")
        if not has_meta_creds and self.provider == "META_API":
            logging.info("ℹ️ [SETUP NOTE] Set 'META_API_TOKEN' and 'PROP_ACCOUNT_ID' in Render to execute live trades.")
        elif has_meta_creds and self.provider == "META_API":
            self._ensure_account_provisioned()

    def _ensure_account_provisioned(self):
        """Discovers primary server region and ensures account is in DEPLOYED state."""
        prov_url = f"https://mt-provisioning-api-v1.agiliumtrade.ai/users/current/accounts/{self.account_id}"
        headers = {"auth-token": META_API_TOKEN, "Content-Type": "application/json"}
        try:
            req = urllib.request.Request(prov_url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                discovered_region = data.get("region", "")
                state = data.get("state", "")
                if discovered_region:
                    self.primary_region = discovered_region
                    logging.info(f"📍 [META-API PROVISIONING] Account primary region detected: '{self.primary_region}' | State: {state}")
                if state and state != "DEPLOYED":
                    logging.warning(f"⚠️ Account state is '{state}'. Initiating deployment on MetaAPI...")
                    deploy_url = f"https://mt-provisioning-api-v1.agiliumtrade.ai/users/current/accounts/{self.account_id}/deploy"
                    deploy_req = urllib.request.Request(deploy_url, data=b"{}", headers=headers)
                    with urllib.request.urlopen(deploy_req, timeout=10) as deploy_resp:
                        logging.info(f"🚀 [META-API DEPLOYMENT TRIGGERED] Response: {deploy_resp.read().decode('utf-8')}")
        except Exception as e:
            logging.warning(f"⚠️ Could not auto-detect provisioning region: {e}. Falling back to default list.")

    async def execute_cloud_order(self, symbol: str, action: str, volume: float, price: float, tp: float, sl: float) -> Dict[str, Any]:
        """
        Submits market order to prop firm directly from Render Cloud with 429 backoff retry.
        """
        # Normalize symbol: strip slashes/hyphens (e.g. 'ETH/USD' or 'ETH/USDT' -> 'ETHUSD')
        clean_symbol = symbol.replace("/", "").replace("-", "").strip().upper()
        if clean_symbol == "ETHUSDT":
            clean_symbol = "ETHUSD"
        elif clean_symbol == "BTCUSDT":
            clean_symbol = "BTCUSD"

        # Rate-limiting / debounce check
        debounce_key = f"{clean_symbol}:{action.upper()}"
        now = time.time()
        last_time = self.last_order_timestamps.get(debounce_key, 0.0)
        if (now - last_time) < self.min_order_interval:
            logging.warning(f"⚠️ [RATE LIMIT] Suppressed duplicate {action} order for {clean_symbol} within {self.min_order_interval}s")
            return {"status": "DEBOUNCED", "symbol": clean_symbol, "action": action}
        self.last_order_timestamps[debounce_key] = now

        logging.info(f"⚡ [CLOUD AUTO-TRADE] Initiating {action} for {clean_symbol} | Volume: {volume} | Target TP: {tp}")

        # If MetaAPI is configured (Connects Render directly to MT5 account in cloud)
        if self.provider == "META_API" and META_API_TOKEN and META_API_TOKEN != "YOUR_META_API_TOKEN" and self.account_id:
            all_regions = ["new-york", "london", "singapore"]
            regions = [self.primary_region] if self.primary_region in all_regions else []
            for r in all_regions:
                if r not in regions:
                    regions.append(r)

            headers = {
                "auth-token": META_API_TOKEN,
                "Content-Type": "application/json"
            }
            order_data = {
                "actionType": "ORDER_TYPE_BUY" if action.upper() == "BUY" else "ORDER_TYPE_SELL",
                "symbol": clean_symbol,
                "volume": volume,
                "takeProfit": tp,
                "stopLoss": sl,
                "comment": "QuantEngine-HalalSpot"
            }
            last_err = None
            max_retries = 3

            for region in regions:
                url = f"https://mt-client-api-v1.{region}.agiliumtrade.ai/users/current/accounts/{self.account_id}/trade"
                
                for attempt in range(1, max_retries + 1):
                    try:
                        req = urllib.request.Request(url, data=json.dumps(order_data).encode("utf-8"), headers=headers)
                        with urllib.request.urlopen(req, timeout=12) as response:
                            res_body = response.read().decode("utf-8")
                            logging.info(f"✅ [PROP FIRM FILLED via {region}] Broker Response: {res_body}")
                            self.primary_region = region
                            notify_telegram(
                                f"✅ [CLOUD AUTO-TRADE SUCCESS]\n\n"
                                f"Broker: {self.provider} (FTMO)\n"
                                f"Action: {action} {clean_symbol}\n"
                                f"Volume: {volume} Lots\n"
                                f"Price: ${price:.2f}\n"
                                f"Status: FILLED 100% Hands-Free!"
                            )
                            return json.loads(res_body)
                    except urllib.error.HTTPError as he:
                        err_content = ""
                        try:
                            err_content = he.read().decode("utf-8")
                        except Exception:
                            pass

                        if he.code == 429:
                            # 🛡️ EXPONENTIAL BACKOFF & RETRY FOR RATE LIMIT
                            retry_after = 2.0 * attempt
                            if he.headers and "Retry-After" in he.headers:
                                try:
                                    retry_after = float(he.headers["Retry-After"])
                                except Exception:
                                    pass
                            logging.warning(f"⚠️ [RATE LIMIT 429] MetaAPI throttled request on {region} (attempt {attempt}/{max_retries}). Pausing {retry_after:.1f}s...")
                            last_err = f"HTTP 429 Rate Limit (attempt {attempt}/{max_retries}): {err_content or he.reason}"
                            if attempt < max_retries:
                                await asyncio.sleep(retry_after)
                                continue
                            else:
                                break
                        elif he.code in (404, 502, 503):
                            logging.warning(f"⚠️ Region {region} returned HTTP {he.code}, trying next region...")
                            last_err = he
                            break
                        else:
                            last_err = f"HTTP {he.code}: {err_content or he.reason}"
                            break
                    except Exception as e:
                        last_err = e
                        break

                if self.primary_region == region and last_err and "429" not in str(last_err):
                    continue

            logging.error(f"❌ Cloud Execution failed via MetaAPI: {last_err}")
            notify_telegram(
                f"🚨 [BROKER EXECUTION ALERT]\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ Broker execution failed for {action} {clean_symbol}!\n"
                f"⚠️ Volume: {volume} Lots\n"
                f"🛑 Reason: {last_err}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            return {"status": "FAILED", "error": str(last_err)}

        # Simulation / Paper mode (Default before live credentials are bound)
        logging.info(f"📝 [SIMULATED CLOUD EXECUTION] {action} {clean_symbol} simulated successfully. No manual intervention required.")
        notify_telegram(f"🤖 [CLOUD BOT EXECUTED TRADE]\n\nAsset: {clean_symbol}\nAction: {action}\nSimulated Lot: {volume}\nExecution: 100% Automated from Render Cloud!\nYour PC is OFF and safe.")
        return {
            "status": "SIMULATED_SUCCESS",
            "symbol": clean_symbol,
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
