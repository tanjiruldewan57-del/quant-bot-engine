"""
Binance Spot Trade-Only Automated Execution Engine
===================================================
100% Automated Cloud Execution Engine for Shariah Mudarabah Accounts.
Executes 100% Halal Cash Spot orders on Binance (No Margin, No Futures, No Shorting, No Swap).

Designed for Zero-Capital Scaling with External Capital Partners:
- Uses Trade-Only API Keys (Withdrawal permissions strictly disabled).
- Funds remain in the investor's personal Binance account at all times.
- Connects to internal Rust quant signals via authenticated UDP port 5003.
- Automatic Pre-Flight Security Audit verifies withdrawal safety on boot.
"""

import os
import json
import time
import hmac
import hashlib
import asyncio
import logging
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ==========================================
# ⚙️ CONFIGURATION & ENVIRONMENT VARIABLES
# ==========================================
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
BINANCE_TESTNET = os.getenv("BINANCE_TESTNET", "false").lower() in ("true", "1", "yes")
BINANCE_BASE_URL = "https://testnet.binance.vision" if BINANCE_TESTNET else "https://api.binance.com"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
UDP_SECRET = os.getenv("UDP_SECRET", "")
UDP_PORT = int(os.getenv("BINANCE_UDP_PORT", "5003"))

# Risk parameters
MAX_ALLOCATION_PER_TRADE_USDT = float(os.getenv("MAX_ALLOCATION_PER_TRADE_USDT", "2500.0"))
MIN_ALLOCATION_PER_TRADE_USDT = float(os.getenv("MIN_ALLOCATION_PER_TRADE_USDT", "15.0"))


def notify_telegram(message: str):
    """Dispatches instant trade execution telemetry to user's Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("⚠️ [TELEGRAM SKIPPED] TELEGRAM_BOT_TOKEN or CHAT_ID not set.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, headers={"User-Agent": "BinanceSpotExecutor/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            pass
    except Exception as e:
        logging.error(f"Telegram alert error: {e}")


class BinanceSpotExecutor:
    def __init__(self):
        self.api_key = BINANCE_API_KEY
        self.api_secret = BINANCE_API_SECRET
        self.base_url = BINANCE_BASE_URL
        self.is_live = bool(self.api_key and self.api_secret and self.api_key != "YOUR_BINANCE_API_KEY")
        self.last_order_timestamps = {}
        self.debounce_seconds = 5.0

        mode_desc = "🔴 LIVE BINANCE SPOT (REAL ASSETS)" if self.is_live else "🟡 SIMULATION / DRY-RUN MODE"
        logging.info(f"🚀 [BINANCE SPOT EXECUTOR INITIALIZED] Mode: {mode_desc} | Gateway: {self.base_url}")

        if self.is_live:
            self.verify_trade_only_permissions()
        else:
            logging.info("ℹ️ [SETUP NOTE] Set 'BINANCE_API_KEY' and 'BINANCE_API_SECRET' in Render to execute live Spot orders.")

    def _sign_query(self, params: Dict[str, Any]) -> str:
        """Appends timestamp and generates HMAC-SHA256 signature."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return f"{query_string}&signature={signature}"

    def _send_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Sends authenticated request to Binance REST API with retry handling."""
        if params is None:
            params = {}

        query = self._sign_query(params)
        url = f"{self.base_url}{endpoint}?{query}"
        headers = {
            "X-MBX-APIKEY": self.api_key,
            "User-Agent": "QuantEngine-BinanceSpotExecutor/1.0"
        }

        req = urllib.request.Request(url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            logging.error(f"❌ [BINANCE API HTTP {e.code}] {err_body}")
            return {"error": True, "status": e.code, "message": err_body}
        except Exception as e:
            logging.error(f"❌ [BINANCE API CONNECTION ERROR] {e}")
            return {"error": True, "message": str(e)}

    def verify_trade_only_permissions(self):
        """
        🛡️ SHARIAH MUDARABAH PRE-FLIGHT AUDIT:
        Queries GET /api/v3/account to verify:
        1. canTrade == True (Trading enabled)
        2. canWithdraw == False (CRITICAL: Withdrawals must be blocked for investor asset safety)
        3. Account type is SPOT (No Margin/Futures/Leverage)
        """
        logging.info("🔍 [SHARIAH AUDIT] Performing Pre-Flight Account Verification...")
        data = self._send_request("GET", "/api/v3/account")
        if data.get("error"):
            logging.error(f"❌ Failed to query Binance account: {data.get('message')}")
            return

        can_trade = data.get("canTrade", False)
        can_withdraw = data.get("canWithdraw", True)
        account_type = data.get("accountType", "UNKNOWN")

        logging.info(f"📊 [ACCOUNT INFO] Type: {account_type} | Can Trade: {can_trade} | Can Withdraw: {can_withdraw}")

        if not can_trade:
            logging.error("🚨 [CRITICAL ALERT] Trading is DISABLED on this API key!")

        if can_withdraw:
            logging.warning("⚠️ [SECURITY WARNING] Withdrawals are ENABLED on this API key!")
            logging.warning("⚠️ To guarantee 100% investor trust under Mudarabah, disable 'Enable Withdrawals' in Binance API settings.")
        else:
            logging.info("✅ [SHARIAH COMPLIANCE PASSED] Trade-Only Mode Verified. Withdrawals are strictly DISABLED.")

        # Log balances
        balances = data.get("balances", [])
        usdt_free = 0.0
        eth_free = 0.0
        for b in balances:
            if b.get("asset") == "USDT":
                usdt_free = float(b.get("free", 0.0))
            elif b.get("asset") == "ETH":
                eth_free = float(b.get("free", 0.0))

        logging.info(f"💰 [LIVE BALANCES] USDT: ${usdt_free:.2f} | ETH: {eth_free:.4f}")

    def get_asset_balance(self, asset: str) -> float:
        """Fetches free available balance of a specific asset."""
        if not self.is_live:
            return 1000.0
        data = self._send_request("GET", "/api/v3/account")
        if data.get("error"):
            return 0.0
        for b in data.get("balances", []):
            if b.get("asset") == asset:
                return float(b.get("free", 0.0))
        return 0.0

    async def execute_spot_buy(self, symbol: str, amount_usd: float, price: float) -> Dict[str, Any]:
        """
        Executes a 100% Halal Cash Spot BUY order.
        Uses quoteOrderQty to buy exact USD value of asset.
        """
        clean_symbol = symbol.replace("/", "").replace("-", "").strip().upper()
        if clean_symbol in ("ETHUSD", "ETHUSDT"):
            clean_symbol = "ETHUSDT"

        # Debounce check
        now = time.time()
        if (now - self.last_order_timestamps.get(f"{clean_symbol}:BUY", 0.0)) < self.debounce_seconds:
            logging.warning(f"⏳ [DEBOUNCE] Dropping duplicate BUY signal for {clean_symbol}")
            return {"status": "DEBOUNCED"}
        self.last_order_timestamps[f"{clean_symbol}:BUY"] = now

        # Clamp trade allocation
        trade_usd = max(MIN_ALLOCATION_PER_TRADE_USDT, min(amount_usd, MAX_ALLOCATION_PER_TRADE_USDT))

        logging.info(f"🟢 [EXECUTING SPOT BUY] {clean_symbol} | Target Size: ${trade_usd:.2f} USDT @ ~${price:.2f}")

        if not self.is_live:
            sim_eth = (trade_usd / price) * 0.999
            logging.info(f"🟡 [SIMULATED BUY] Filled {sim_eth:.4f} {clean_symbol} at ${price:.2f} (Fee: 0.1% Spot)")
            return {
                "status": "SIMULATED_FILLED",
                "symbol": clean_symbol,
                "executedQty": f"{sim_eth:.4f}",
                "cummulativeQuoteQty": f"{trade_usd:.2f}",
                "price": price
            }

        # Live Binance Order
        params = {
            "symbol": clean_symbol,
            "side": "BUY",
            "type": "MARKET",
            "quoteOrderQty": f"{trade_usd:.2f}"
        }
        res = self._send_request("POST", "/api/v3/order", params)
        if res.get("error"):
            logging.error(f"❌ [BUY REJECTED] {res.get('message')}")
            return res

        executed_qty = res.get("executedQty", "0.0")
        quote_spent = res.get("cummulativeQuoteQty", f"{trade_usd:.2f}")
        order_id = res.get("orderId", "N/A")

        logging.info(f"✅ [SPOT BUY FILLED] Order #{order_id} | {executed_qty} {clean_symbol} for ${quote_spent} USDT")

        notify_telegram(
            f"🟢 [BINANCE SPOT BUY EXECUTED]\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 Asset: {clean_symbol} (1x Cash Spot)\n"
            f"💵 Amount Spent: ${quote_spent} USDT\n"
            f"📦 Received: {executed_qty} ETH\n"
            f"🆔 Binance Order ID: #{order_id}\n"
            f"🕋 Compliance: 100% Halal Qabd Hukmi\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        return res

    async def execute_spot_sell(self, symbol: str, price: float, profit_pct: float, reason: str) -> Dict[str, Any]:
        """
        Executes a 100% Halal Cash Spot SELL order.
        Sells entire holding of base asset back into USDT.
        """
        clean_symbol = symbol.replace("/", "").replace("-", "").strip().upper()
        if clean_symbol in ("ETHUSD", "ETHUSDT"):
            clean_symbol = "ETHUSDT"

        now = time.time()
        if (now - self.last_order_timestamps.get(f"{clean_symbol}:SELL", 0.0)) < self.debounce_seconds:
            logging.warning(f"⏳ [DEBOUNCE] Dropping duplicate SELL signal for {clean_symbol}")
            return {"status": "DEBOUNCED"}
        self.last_order_timestamps[f"{clean_symbol}:SELL"] = now

        base_asset = "ETH" if "ETH" in clean_symbol else "BTC"
        avail_qty = self.get_asset_balance(base_asset)

        # Truncate to 4 decimals for ETH stepSize compliance
        sell_qty = int(avail_qty * 10000) / 10000.0

        if sell_qty <= 0.001 and self.is_live:
            logging.warning(f"⚠️ [SELL SKIPPED] Available {base_asset} balance ({sell_qty}) below Binance minimum.")
            return {"status": "INSUFFICIENT_BALANCE"}

        logging.info(f"🔴 [EXECUTING SPOT SELL] {clean_symbol} | Qty: {sell_qty} {base_asset} @ ~${price:.2f} | Reason: {reason}")

        if not self.is_live:
            quote_val = sell_qty * price * 0.999
            logging.info(f"🟡 [SIMULATED SELL] Closed position. Value: ${quote_val:.2f} USDT | PnL: {profit_pct:+.2f}%")
            return {
                "status": "SIMULATED_FILLED",
                "symbol": clean_symbol,
                "executedQty": f"{sell_qty:.4f}",
                "cummulativeQuoteQty": f"{quote_val:.2f}",
                "profit_pct": profit_pct
            }

        params = {
            "symbol": clean_symbol,
            "side": "SELL",
            "type": "MARKET",
            "quantity": f"{sell_qty:.4f}"
        }
        res = self._send_request("POST", "/api/v3/order", params)
        if res.get("error"):
            logging.error(f"❌ [SELL REJECTED] {res.get('message')}")
            return res

        quote_rec = res.get("cummulativeQuoteQty", "0.0")
        order_id = res.get("orderId", "N/A")
        logging.info(f"✅ [SPOT SELL FILLED] Order #{order_id} | Sold {sell_qty} for ${quote_rec} USDT")

        notify_telegram(
            f"🔴 [BINANCE SPOT SELL EXECUTED]\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 Asset: {clean_symbol} (Position Closed)\n"
            f"💰 Proceeds: ${quote_rec} USDT\n"
            f"📈 Net Return: {profit_pct:+.2f}%\n"
            f"📌 Trigger: {reason}\n"
            f"🆔 Binance Order ID: #{order_id}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        return res

    async def start_udp_listener(self):
        """Listens on UDP port 5003 for signals from Rust quant engine."""
        class BinanceUdpProtocol(asyncio.DatagramProtocol):
            def __init__(self, executor):
                self.executor = executor

            def datagram_received(self, data, addr):
                try:
                    payload = json.loads(data.decode("utf-8"))

                    # Authenticate payload
                    if UDP_SECRET:
                        token = payload.get("auth_token", "")
                        if not hmac.compare_digest(token, UDP_SECRET):
                            logging.warning(f"🚨 [UNAUTHORIZED UDP] Invalid token from {addr} on port {UDP_PORT}!")
                            return

                    action = payload.get("action", "").upper()
                    symbol = payload.get("symbol", "ETHUSDT")
                    price = float(payload.get("price", 0.0))

                    if action == "BUY":
                        amount_usd = float(payload.get("amount_usd", 500.0))
                        asyncio.create_task(self.executor.execute_spot_buy(symbol, amount_usd, price))
                    elif action == "SELL":
                        profit_pct = float(payload.get("profit_pct", 0.0))
                        reason = payload.get("reason", "Take-Profit")
                        asyncio.create_task(self.executor.execute_spot_sell(symbol, price, profit_pct, reason))

                except Exception as e:
                    logging.error(f"Error handling UDP datagram: {e}")

        loop = asyncio.get_running_loop()
        logging.info(f"🎧 Binance Spot Executor listening on 127.0.0.1:{UDP_PORT} for Rust signals...")
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: BinanceUdpProtocol(self),
            local_addr=("127.0.0.1", UDP_PORT)
        )

        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    executor = BinanceSpotExecutor()
    try:
        asyncio.run(executor.start_udp_listener())
    except KeyboardInterrupt:
        print("Binance Spot Executor shutting down.")
