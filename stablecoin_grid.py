import websocket
import json
import socket
import time

class StablecoinGridBot:
    def __init__(self):
        # বাইন্যান্সের লাইভ ওয়েবসকেট (USDC/USDT পেয়ার)
        self.ws_url = "wss://stream.binance.us:9443/ws/usdcusdt@bookTicker"
        
        self.udp_ip = "127.0.0.1"
        self.udp_port = 5000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # জিরো-রিস্ক ম্যাথ: 0.9995 এ নামলে কিনবে, 1.0005 এ উঠলে সেল করবে
        self.buy_threshold = 0.9995  
        self.sell_threshold = 1.0005 
        
        print("[STABLECOIN BOT] Armed and monitoring USDC/USDT Peg at Nano-second speed...")

    def send_signal_to_rust(self, action, price):
        score = 1.0 if action == "BUY" else -1.0
        signal_data = {
            "source": "STABLECOIN_GRID",
            "timestamp": time.time(),
            "headline": f"STABLECOIN ARB: {action} USDC at {price}",
            "sentiment_score": score
        }
        message = json.dumps(signal_data).encode('utf-8')
        self.sock.sendto(message, (self.udp_ip, self.udp_port))
        print(f"⚡ [SIGNAL SENT] {action} USDC/USDT @ {price}")

    def on_message(self, ws, message):
        data = json.loads(message)
        ask_price = float(data['a'])
        bid_price = float(data['b'])

        if ask_price <= self.buy_threshold:
            print(f"🚨 [DE-PEG DETECTED] USDC is cheap! Ask: {ask_price}")
            self.send_signal_to_rust("BUY", ask_price)
            time.sleep(10) 
            
        elif bid_price >= self.sell_threshold:
            print(f"🚨 [PREMIUM DETECTED] USDC is expensive! Bid: {bid_price}")
            self.send_signal_to_rust("SELL", bid_price)
            time.sleep(10)

    def on_error(self, ws, error):
        print(f"[ERROR] {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("[CLOSED] Reconnecting in 3 seconds...")
        time.sleep(3)
        self.run()

    def run(self):
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        ws.run_forever()

if __name__ == "__main__":
    bot = StablecoinGridBot()
    bot.run()