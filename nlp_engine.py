import time
import json
import socket
import urllib.request
import xml.etree.ElementTree as ET
import nltk

try:
    nltk.data.find('sentiment/vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

from nltk.sentiment.vader import SentimentIntensityAnalyzer

class NLPSentimentSniper:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.udp_ip = "127.0.0.1"
        self.udp_port = 5000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.news_sources = [
            "https://cointelegraph.com/rss",
            "https://www.coindesk.com/arc/outboundfeeds/rss/"
        ]
        self.seen_news = set()
        print("[NLP BOT] Starting Sentiment Sniper Microservice...")

    def fetch_news(self):
        headlines = []
        for url in self.news_sources:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    xml_data = response.read()
                    root = ET.fromstring(xml_data)
                    for item in root.findall('.//item/title'):
                        title = item.text
                        if title not in self.seen_news:
                            self.seen_news.add(title)
                            headlines.append(title)
            except Exception as e:
                pass
        return headlines

    def analyze_and_send(self, headlines):
        for text in headlines:
            scores = self.analyzer.polarity_scores(text)
            compound_score = scores['compound']
            
            # সিগন্যাল ট্রিগার ফিল্টার
            if compound_score >= 0.5 or compound_score <= -0.5:
                signal_data = {
                    "source": "NLP_BOT",
                    "timestamp": time.time(),
                    "headline": text,
                    "sentiment_score": compound_score
                }
                
                # Rust ইঞ্জিনে সিগন্যাল পাঠানো হচ্ছে
                message = json.dumps(signal_data).encode('utf-8')
                self.sock.sendto(message, (self.udp_ip, self.udp_port))
                print(f"[ALERT] Sent to Rust -> Score: {compound_score:.2f} | News: {text}")

    def run(self):
        while True:
            new_headlines = self.fetch_news()
            if new_headlines:
                self.analyze_and_send(new_headlines)
            time.sleep(60) # ৬০ সেকেন্ড স্লিপ (CPU 0% রাখার জন্য)

if __name__ == "__main__":
    bot = NLPSentimentSniper()
    bot.run()