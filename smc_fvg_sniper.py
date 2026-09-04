import json
import socket
import time
import requests

class SMCSniperBot:
    def __init__(self):
        # Fetching the last 15 candles (15-minute timeframe is highly accurate for FVG)
        self.klines_url = "https://api.binance.us/api/v3/klines?symbol=ETHUSDT&interval=15m&limit=15"
        
        # UDP Connection to the Main Rust Engine
        self.udp_ip = "127.0.0.1"
        self.udp_port = 5000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        print("[SMC BOT 8] Armed! Scanning charts for Fair Value Gaps (FVG) and Smart Money Footprints...")

    def fetch_candles(self):
        try:
            res = requests.get(self.klines_url, timeout=5).json()
            # We need: Open, High, Low, Close for each candle
            candles = []
            for c in res:
                candles.append({
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4])
                })
            return candles
        except Exception:
            return None

    def scan_fvg(self):
        candles = self.fetch_candles()
        if not candles or len(candles) < 3:
            return

        current_price = candles[-1]['close']
        
        # Look for FVG in the previous candles (excluding the current forming candle)
        fvg_found = False
        
        for i in range(len(candles) - 3):
            c1 = candles[i]
            c2 = candles[i+1] # The large impulse candle
            c3 = candles[i+2]
            
            # 1. Bullish FVG (Price pumped hard, leaving a gap)
            # Gap exists if C1 High is strictly less than C3 Low
            if c1['high'] < c3['low'] and c2['close'] > c2['open']:
                gap_top = c3['low']
                gap_bottom = c1['high']
                
                # Check if the CURRENT price has pulled back into this gap (The Sniper Entry!)
                if gap_bottom <= current_price <= gap_top:
                    fvg_found = True
                    print(f"🎯 [BULLISH FVG HIT] Price pulled back into Institutional Gap (${gap_bottom:.2f} - ${gap_top:.2f})")
                    self.send_signal_to_rust("BUY", 1.0)
                    time.sleep(30) # Cooldown
            
            # 2. Bearish FVG (Price dumped hard, leaving a gap)
            # Gap exists if C1 Low is strictly greater than C3 High
            elif c1['low'] > c3['high'] and c2['close'] < c2['open']:
                gap_bottom = c3['high']
                gap_top = c1['low']
                
                # Check if the CURRENT price has pumped back into this gap (Sniper Entry!)
                if gap_bottom <= current_price <= gap_top:
                    fvg_found = True
                    print(f"🎯 [BEARISH FVG HIT] Price pumped into Institutional Gap (${gap_bottom:.2f} - ${gap_top:.2f})")
                    self.send_signal_to_rust("SELL", -1.0)
                    time.sleep(30) # Cooldown
                    
        if not fvg_found:
            print(f"👁️ Scanning... Current Price: ${current_price:.2f} | No FVG pullbacks detected yet.")

    def send_signal_to_rust(self, action, score):
        signal_data = {
            "source": "SMC_FVG",
            "timestamp": time.time(),
            "headline": f"SMC SNIPER: FVG {action} ZONE HIT!",
            "sentiment_score": score
        }
        message = json.dumps(signal_data).encode('utf-8')
        self.sock.sendto(message, (self.udp_ip, self.udp_port))
        print(f"⚡ [SIGNAL SENT] Rust Engine Activated for FVG Sniper {action}!")

    def run(self):
        while True:
            self.scan_fvg()
            # Scan every 5 seconds
            time.sleep(5)

if __name__ == "__main__":
    bot = SMCSniperBot()
    bot.run()