import requests
import json
import socket
import time

class L2OrderBookBot:
    def __init__(self):
        # We will scan the top 20 levels of the ETH/USDT Order Book (Level 2 Data)
        self.depth_url = "https://api.binance.us/api/v3/depth?symbol=ETHUSDT&limit=20"
        
        # UDP Connection to the Main Rust Engine
        self.udp_ip = "127.0.0.1"
        self.udp_port = 5000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Imbalance Thresholds
        # Imbalance ranges from -1.0 (100% Sellers) to +1.0 (100% Buyers)
        # 0.50 means there is 3x more Buy Volume than Sell Volume (Massive Buy Wall)
        self.imbalance_threshold = 0.50 
        
        print("[L2 ORDER-BOOK BOT] Armed! Scanning Market Depth for Institutional Liquidity Walls...")

    def fetch_orderbook(self):
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(self.depth_url, headers=headers, timeout=5).json()
            return res.get('bids', []), res.get('asks', [])
        except Exception as e:
            print(f"[API ERROR] {e}")
            return [], []

    def calculate_imbalance(self):
        bids, asks = self.fetch_orderbook()
        
        if not bids or not asks:
            return

        # Calculate Total Buy Volume (Bids) and Sell Volume (Asks)
        total_bid_vol = sum(float(bid[1]) for bid in bids)
        total_ask_vol = sum(float(ask[1]) for ask in asks)
        
        total_vol = total_bid_vol + total_ask_vol
        if total_vol == 0:
            return

        # Mathematical Imbalance Formula
        imbalance = (total_bid_vol - total_ask_vol) / total_vol

        print(f"📊 Buy Wall: {total_bid_vol:.2f} ETH | Sell Wall: {total_ask_vol:.2f} ETH | Imbalance: {imbalance:+.2f}")

        # If there is a massive Buy Wall (Imbalance > +0.50)
        if imbalance >= self.imbalance_threshold:
            print(f"🚨 [LIQUIDITY WALL DETECTED] Massive BUY WALL found! Imbalance: {imbalance:+.2f}")
            self.send_signal_to_rust("BUY", 1.0)
            time.sleep(10)
            
        # If there is a massive Sell Wall (Imbalance < -0.50)
        elif imbalance <= -self.imbalance_threshold:
            print(f"🚨 [DUMP DETECTED] Massive SELL WALL found! Imbalance: {imbalance:+.2f}")
            self.send_signal_to_rust("SELL", -1.0)
            time.sleep(10)

    def send_signal_to_rust(self, action, score):
        signal_data = {
            "source": "L2_ORDERBOOK",
            "timestamp": time.time(),
            "headline": f"ORDERBOOK IMBALANCE: {action} WALL DETECTED!",
            "sentiment_score": score
        }
        message = json.dumps(signal_data).encode('utf-8')
        self.sock.sendto(message, (self.udp_ip, self.udp_port))
        print(f"⚡ [SIGNAL SENT] Rust Engine Activated for {action}!")

    def run(self):
        while True:
            self.calculate_imbalance()
            # Scan the orderbook every 3 seconds
            time.sleep(3)

if __name__ == "__main__":
    bot = L2OrderBookBot()
    bot.run()