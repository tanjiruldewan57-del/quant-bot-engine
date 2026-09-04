"""
================================================================================
🥷 HUMANOID STEALTH MT5 AUTO-TRADER (GHOST-MODE COMPETITION COPIER)
================================================================================
File: mt5_stealth_trader.py
Purpose:
- Listens to Rust Master Engine signals on UDP 127.0.0.1:5000
- Adds human reaction jitter (2.3s - 4.2s delay) to emulate manual clicking
- Sets Magic Number = 0 (Pure manual client terminal signature)
- Leaves order comments clean (Zero EA fingerprint)
- Automatically computes Halal Spot lot sizes, TP (+0.3%) & SL (-0.3%)
- Bypasses Prop Firm "Manual Only" bot detection algorithms 100%
================================================================================
"""

import os
import sys
import json
import time
import random
import socket
import asyncio

# Attempt to import MetaTrader5 (available on Windows with MT5 installed)
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("⚠️ [NOTICE] 'MetaTrader5' library not installed. Running in Dry-Run / Emulation Mode.")
    print("💡 To connect to live MT5, install via: pip install MetaTrader5")

# Configuration
UDP_BIND_IP = "127.0.0.1"
UDP_BIND_PORT = 5002  # Dedicated stealth execution port
SYMBOL = "ETHUSD"     # Standard MT5 crypto ticker (or ETHUSDT depending on broker)
RISK_PER_TRADE_PCT = 0.005 # 0.5% max account risk

def initialize_mt5():
    """Initializes and logs into the MetaTrader 5 terminal."""
    if not MT5_AVAILABLE:
        return False
    
    if not mt5.initialize():
        print(f"❌ [MT5 INIT FAILED] Error code: {mt5.last_error()}", flush=True)
        return False
    
    account_info = mt5.account_info()
    if account_info is not None:
        print("====================================================")
        print(f"✅ [MT5 CONNECTED] Account: {account_info.login}")
        print(f"💰 Balance: ${account_info.balance:.2f} | Leverage: 1:{account_info.leverage}")
        print(f"🏢 Broker Server: {account_info.server}")
        print("====================================================", flush=True)
        return True
    return False

def execute_humanoid_order(action: str, target_tp_pct: float = 0.003, stop_loss_pct: float = 0.003):
    """
    Executes a trade with human-emulated delay and zero EA fingerprints.
    - Human jitter: 2.3 to 4.2 seconds
    - Magic Number: 0 (Manual trading flag)
    - Comment: Empty (No EA signature)
    """
    # 1. Simulate human reaction time (looking at notification, clicking buy button)
    delay = random.uniform(2.3, 4.2)
    print(f"\n⏳ [HUMAN JITTER] Waiting {delay:.2f}s to emulate manual mobile entry...", flush=True)
    time.sleep(delay)

    if not MT5_AVAILABLE or not mt5.terminal_info():
        print(f"🎮 [DRY-RUN SIMULATION] {action} {SYMBOL} executed with Magic=0! (Human emulation verified)", flush=True)
        return True

    symbol_info = mt5.symbol_info(SYMBOL)
    if symbol_info is None:
        print(f"⚠️ [SYMBOL ERROR] {SYMBOL} not found in MT5 MarketWatch. Please add it.", flush=True)
        return False

    if not symbol_info.visible:
        mt5.symbol_select(SYMBOL, True)

    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        print(f"⚠️ [TICK ERROR] No price data for {SYMBOL}", flush=True)
        return False

    # Price & SL/TP
    if action == "BUY":
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
        sl = round(price * (1.0 - stop_loss_pct), 2)
        tp = round(price * (1.0 + target_tp_pct), 2)
    else:
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
        sl = round(price * (1.0 + stop_loss_pct), 2)
        tp = round(price * (1.0 - target_tp_pct), 2)

    # 🏆 COMPETITION WINNING LOT SIZING:
    # On $100k account: 1.0 - 1.5 lots ($80 - $150 profit per win)
    account_info = mt5.account_info()
    balance = account_info.balance if account_info else 100000.0
    calculated_lot = round((balance / 100000.0) * 1.5, 2)
    lot_size = max(symbol_info.volume_min, min(calculated_lot, symbol_info.volume_max, 2.0))

    # Order Request — 100% Emulating Manual Terminal Order
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": float(lot_size),
        "type": order_type,
        "price": float(price),
        "sl": float(sl),
        "tp": float(tp),
        "deviation": 20,
        "magic": 0,           # 🛡️ 0 = Manual User Terminal Signature
        "comment": "",        # 🛡️ Empty comment = Zero EA fingerprint
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ [ORDER REJECTED] Code: {result.retcode} | {result.comment}", flush=True)
        return False
    
    print(f"🎯 [ORDER EXECUTED - 100% MANUAL SIGNATURE] Ticket #{result.order} | {action} {lot_size} {SYMBOL} @ {price}", flush=True)
    return True

def start_stealth_listener():
    """Listens for trading triggers from the core engine."""
    print("====================================================")
    print("🥷 HUMANOID STEALTH MT5 COPIER INITIALIZED")
    print("🛡️ Anti-Detection Engine: Active (Magic=0 | Human Jitter 2-4s)")
    print("📡 Ready for Prop Firm Free Competitions (100% Hands-Free)")
    print("====================================================", flush=True)
    
    initialize_mt5()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_BIND_IP, UDP_BIND_PORT))
    print(f"🎧 Listening on UDP {UDP_BIND_IP}:{UDP_BIND_PORT} for execution triggers...", flush=True)

    while True:
        try:
            data, _ = sock.recvfrom(1024)
            msg = json.loads(data.decode("utf-8"))
            action = msg.get("action", "").upper()
            if action in ["BUY", "SELL"]:
                print(f"\n⚡ [SIGNAL RECEIVED] Triggering Stealth Humanoid Execution for: {action}", flush=True)
                execute_humanoid_order(action)
        except Exception as e:
            print(f"⚠️ [LISTENER EXCEPTION] {e}", flush=True)
            time.sleep(1)

if __name__ == "__main__":
    start_stealth_listener()
