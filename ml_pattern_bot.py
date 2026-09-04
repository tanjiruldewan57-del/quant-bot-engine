import json
import socket
import time
import requests
import math

class LightweightNeuralNetBot:
    def __init__(self):
        # We will use Binance Klines (Candlesticks) data
        self.klines_url = "https://api.binance.us/api/v3/klines?symbol=ETHUSDT&interval=1m&limit=10"
        
        self.udp_ip = "127.0.0.1"
        self.udp_port = 5000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Neural Network Weights (Randomly initialized, will auto-adjust)
        self.weights = [0.2, 0.4, 0.6, 0.8, 0.5]
        self.learning_rate = 0.01
        
        print("[AI BOT 7] Armed! Running Custom Raw-Python Neural Network (Zero RAM)...")

    def fetch_recent_prices(self):
        try:
            res = requests.get(self.klines_url, timeout=5).json()
            # Extract closing prices
            prices = [float(candle[4]) for candle in res]
            return prices
        except Exception:
            return None

    def sigmoid(self, x):
        # Activation function
        return 1 / (1 + math.exp(-x))

    def predict_and_train(self):
        prices = self.fetch_recent_prices()
        if not prices or len(prices) < 6:
            return

        # We take the last 5 prices as input to predict the 6th (latest) price direction
        inputs = prices[-6:-1]
        actual_latest = prices[-1]

        # Normalize inputs (0 to 1 range based on the minimum price)
        base_price = min(inputs)
        norm_inputs = [(p - base_price) / base_price for p in inputs]
        
        # Forward Pass (Predict)
        prediction_value = sum(i * w for i, w in zip(norm_inputs, self.weights))
        prediction = self.sigmoid(prediction_value)

        # Did price actually go up or down? (1.0 for UP, 0.0 for DOWN)
        actual_direction = 1.0 if actual_latest > inputs[-1] else 0.0
        
        # Calculate Error
        error = actual_direction - prediction
        
        # Backpropagation (Train/Update Weights)
        for i in range(len(self.weights)):
            self.weights[i] += self.learning_rate * error * norm_inputs[i]

        print(f"🧠 [AI PREDICTION] Probability of PUMP: {prediction*100:.1f}% | Actual: {'UP' if actual_direction==1 else 'DOWN'}")

        # Signal Rust Engine if prediction is highly confident
        if prediction > 0.80:
            print(f"🚨 [AI CONFIDENCE HIGH] Predicting PUMP!")
            self.send_signal_to_rust("BUY", 0.9)
            time.sleep(10)
        elif prediction < 0.20:
            print(f"🚨 [AI CONFIDENCE HIGH] Predicting DUMP!")
            self.send_signal_to_rust("SELL", -0.9)
            time.sleep(10)

    def send_signal_to_rust(self, action, score):
        signal_data = {
            "source": "AI_PATTERN",
            "timestamp": time.time(),
            "headline": f"AI NEURAL NET: PREDICTING {action}!",
            "sentiment_score": score
        }
        message = json.dumps(signal_data).encode('utf-8')
        self.sock.sendto(message, (self.udp_ip, self.udp_port))
        print(f"⚡ [SIGNAL SENT] Rust Engine Activated for {action}!")

    def run(self):
        while True:
            self.predict_and_train()
            # Run every 60 seconds (1-minute candles)
            time.sleep(60)

if __name__ == "__main__":
    bot = LightweightNeuralNetBot()
    bot.run()