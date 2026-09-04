import requests
import json
import socket
import time

class CexDexArbitrageBot:
    def __init__(self):
        self.binance_url = "https://api.binance.us/api/v3/ticker/price?symbol=ETHUSDT"
        self.dex_url = "https://api.dexscreener.com/latest/dex/pairs/ethereum/0x11b815efb8f581194ae79006d24e0d814b7697f6"
        
        self.udp_ip = "127.0.0.1"
        self.udp_port = 5000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.min_profit_spread_pct = 0.50 
        print("[CEX-DEX BOT] Armed! Monitoring Binance vs Uniswap for Arbitrage Spreads...")

    def fetch_prices(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        try:
            binance_res = requests.get(self.binance_url, headers=headers, timeout=5).json()
            cex_price = float(binance_res['price'])
            
            dex_res = requests.get(self.dex_url, headers=headers, timeout=5).json()
            dex_price = float(dex_res['pairs'][0]['priceUsd'])
            
            return cex_price, dex_price
        except Exception as e:
            print(f"[API ERROR] {e}")
            return None, None

    def analyze_arbitrage(self):
        cex_price, dex_price = self.fetch_prices()
        
        if not cex_price or not dex_price:
            return

        price_diff = abs(dex_price - cex_price)
        spread_pct = (price_diff / cex_price) * 100

        print(f"📊 Binance: ${cex_price:.2f} | Uniswap: ${dex_price:.2f} | Spread: {spread_pct:.3f}%")

        if spread_pct >= self.min_profit_spread_pct:
            direction = "Buy on Binance -> Sell on Uniswap" if cex_price < dex_price else "Buy on Uniswap -> Sell on Binance"
            print(f"🚨 [ARBITRAGE FOUND!] {direction} | Profit: {spread_pct:.2f}%")
            
            signal_data = {
                "source": "CEX_DEX_ARB",
                "timestamp": time.time(),
                "headline": f"ARBITRAGE: {direction}",
                "sentiment_score": 0.8  
            }
            message = json.dumps(signal_data).encode('utf-8')
            self.sock.sendto(message, (self.udp_ip, self.udp_port))
            print("⚡ [SIGNAL SENT] Rust Engine Activated for Arbitrage!")
            time.sleep(30)

    # 🛠️ ফিক্স ২: API Rate Limit (Dynamic Sleep) এবং Heartbeat Monitor
    def run(self):
        consecutive_errors = 0
        while True:
            try:
                start_time = time.time()
                
                self.analyze_arbitrage()
                
                # পিং (Ping) ক্যালকুলেট করে স্টেল ডেটা (Stale Data) মনিটর করা
                ping = (time.time() - start_time) * 1000
                print(f"💓 [HEARTBEAT] Ping: {ping:.2f} ms")
                
                consecutive_errors = 0 # সাকসেস হলে এরর কাউন্ট জিরো হয়ে যাবে
                time.sleep(5) # ৫ সেকেন্ড ওয়েট করবে (API Ban থেকে বাঁচতে)
                
            except Exception as e:
                consecutive_errors += 1
                wait_time = 5 * consecutive_errors # এরর হলে ওয়েট টাইম গাণিতিক হারে বাড়বে
                print(f"⚠️ [CONNECTION LOST] Warning! Retrying in {wait_time}s...")
                time.sleep(wait_time)

if __name__ == "__main__":
    bot = CexDexArbitrageBot()
    bot.run()