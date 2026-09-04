"""
================================================================================
🚀 EXTREME-MODE QUANT MICROSERVICE FOR YOUR EXISTING RUST ENGINE
================================================================================
File: extreme_mode_engine.py
Place this file directly in your existing Git repo: `Downloads/quant/`
It transmits 3-Factor institutional signals (RLS-OU + OFI + HMM) 
directly into your Rust Master Aggregator on UDP Port 5000.
Zero changes required to your existing running Rust code!
================================================================================
"""

import asyncio
import json
import socket
import time
import sys
import numpy as np
import websockets

# ANSI Styling
GREEN = "\033[92m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"

# UDP Bridge to your existing Rust Engine (UDP 127.0.0.1:5000)
UDP_IP = "127.0.0.1"
UDP_PORT = 5000
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_signal_to_rust(source, headline, score):
    payload = {
        "source": source,
        "timestamp": time.time(),
        "headline": headline,
        "sentiment_score": score
    }
    msg = json.dumps(payload).encode('utf-8')
    sock.sendto(msg, (UDP_IP, UDP_PORT))
    print(f"\n{GREEN}⚡ [SIGNAL TRANSMITTED TO RUST] Score: {score:.2f} | {headline}{RESET}")

# 1. RLS Ornstein-Uhlenbeck Calibrator
class RLSOuCalibrator:
    def __init__(self, lam=0.995, dt=1.0):
        self.lam = lam
        self.dt = dt
        self.P = np.eye(2) * 1000.0
        self.w = np.array([0.0, 0.95])
        self.last_x = None

    def update(self, x_curr):
        if self.last_x is None:
            self.last_x = x_curr
            return None
        u = np.array([1.0, self.last_x])
        den = self.lam + u.T @ self.P @ u
        K = (self.P @ u) / (den + 1e-12)
        pred_error = x_curr - u.T @ self.w
        self.w += K * pred_error
        self.P = (self.P - np.outer(K, u) @ self.P) / self.lam
        self.w[1] = np.clip(self.w[1], 0.0001, 0.9999)
        a, b = self.w[0], self.w[1]
        theta = -np.log(b) / self.dt
        mu = a / (1.0 - b + 1e-12)
        residual_variance = pred_error ** 2
        sigma = np.sqrt((2.0 * theta * residual_variance) / (1.0 - b**2 + 1e-12))
        self.last_x = x_curr
        return {
            "theta": theta,
            "mu": mu,
            "sigma": sigma,
            "equilibrium_std": np.sqrt((sigma**2) / (2.0 * theta + 1e-12)) if theta > 0 else 1.0
        }

# 2. Top-of-Book OFI Imbalance
class OFICalculator:
    def __init__(self):
        self.prev_bid_px = None
        self.prev_bid_sz = None
        self.prev_ask_px = None
        self.prev_ask_sz = None

    def calculate_imbalance(self, bid_px, bid_sz, ask_px, ask_sz):
        if self.prev_bid_px is None:
            self.prev_bid_px, self.prev_bid_sz = bid_px, bid_sz
            self.prev_ask_px, self.prev_ask_sz = ask_px, ask_sz
            return 0.0
        delta_v_b = bid_sz if bid_px > self.prev_bid_px else (bid_sz - self.prev_bid_sz if bid_px == self.prev_bid_px else -self.prev_bid_sz)
        delta_v_a = ask_sz if ask_px < self.prev_ask_px else (ask_sz - self.prev_ask_sz if ask_px == self.prev_ask_px else -self.prev_ask_sz)
        ofi = delta_v_b - delta_v_a
        avg_depth = 0.5 * (bid_sz + ask_sz)
        ofi_norm = ofi / (avg_depth + 1e-12)
        self.prev_bid_px, self.prev_bid_sz = bid_px, bid_sz
        self.prev_ask_px, self.prev_ask_sz = ask_px, ask_sz
        return ofi_norm

# 3. 2-State HMM Crash Circuit Breaker
class HMMRegimeGate:
    def __init__(self, calm_threshold=0.70):
        self.calm_threshold = calm_threshold
        self.mu_calm, self.sig_calm = 0.0001, 0.001
        self.mu_crash, self.sig_crash = -0.002, 0.015
        self.gamma_calm = 0.95

    def update_regime(self, log_return):
        f_calm = (1.0 / (np.sqrt(2 * np.pi) * self.sig_calm)) * np.exp(-((log_return - self.mu_calm)**2) / (2 * self.sig_calm**2))
        f_crash = (1.0 / (np.sqrt(2 * np.pi) * self.sig_crash)) * np.exp(-((log_return - self.mu_crash)**2) / (2 * self.sig_crash**2))
        total_p = f_calm + f_crash + 1e-12
        self.gamma_calm = f_calm / total_p
        return self.gamma_calm >= self.calm_threshold, self.gamma_calm

async def stream_feed(symbol="ethusdt"):
    uri = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@bookTicker"
    calibrator = RLSOuCalibrator()
    ofi_calc = OFICalculator()
    hmm = HMMRegimeGate()
    last_mid = None

    print(f"\n{CYAN}🛡️ [EXTREME-MODE QUANT] Connected to Binance for {symbol.upper()}. Piping to Rust UDP 5000...{RESET}")

    async with websockets.connect(uri) as ws:
        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                bid_px = float(data['b'])
                bid_sz = float(data['B'])
                ask_px = float(data['a'])
                ask_sz = float(data['A'])
                mid = 0.5 * (bid_px + ask_px)

                log_ret = np.log(mid / last_mid) if last_mid else 0.0
                last_mid = mid

                is_calm, prob_calm = hmm.update_regime(log_ret)
                ou = calibrator.update(mid)
                ofi_norm = ofi_calc.calculate_imbalance(bid_px, bid_sz, ask_px, ask_sz)

                if ou is not None and is_calm:
                    z_score = (mid - ou['mu']) / (ou['equilibrium_std'] + 1e-12)
                    
                    # 🟢 SNIPER ENTRY TRIGGER: Z <= -1.5 and Institutional Order Flow > 0.15
                    if z_score <= -1.5 and ofi_norm >= 0.15:
                        headline = f"EXTREME-MODE SNIPER: {symbol.upper()} Z={z_score:.2f}, OFI={ofi_norm:.2f}"
                        # Sends score >= 0.5 which immediately triggers BUY in your Rust engine!
                        send_signal_to_rust("EXTREME_MODE_QUANT", headline, score=0.95)
                        await asyncio.sleep(5) # Cooldown to prevent spam

                elif not is_calm:
                    # 🛑 CRASH WARNING: Triggers instant protection
                    send_signal_to_rust("EXTREME_MODE_CRASH_GUARD", "HMM CRASH REGIME DETECTED!", score=-0.95)
                    await asyncio.sleep(3)

            except Exception as e:
                await asyncio.sleep(2)
                break

if __name__ == "__main__":
    asyncio.run(stream_feed("ethusdt"))
