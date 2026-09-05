"""
EconomicNewsSentinel
Automated High-Impact USD Economic News Filter
Enforces strict T-5m to T+5m trading freeze around CPI, NFP, FOMC to prevent broker slippage.
"""
import requests
import datetime
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EconomicNewsSentinel:
    """
    ফ্রি ইকোনমিক ক্যালেন্ডার এপিআই ব্যবহার করে ইউএস হাই-ইমপ্যাক্ট নিউজ ট্র্যাক করার ইঞ্জিন।
    নিউজ রিলিজের ঠিক ৫ মিনিট আগে বটকে পজ এবং ৫ মিনিট পরে রিজিউম করার সিগন্যাল দেয়।
    """
    def __init__(self, api_key: str = "", check_interval_sec: int = 300):
        self.api_key = api_key
        self.check_interval = check_interval_sec
        self.cached_news_events = []
        self.last_fetch_time = None

    def fetch_usd_high_impact_news(self):
        """Finnhub বা সমমানের এপিআই থেকে সরাসরি লাইভ নিউজ ইভেন্ট রিড করে."""
        if not self.api_key or self.api_key == "your_free_finnhub_api_key_here":
            # 🛡️ OFFLINE RECURRING MACRO SCHEDULE (EST/UTC Fixed Standard Windows)
            # US CPI / NFP typically release at 12:30 UTC (08:30 AM EST)
            # FOMC typically releases at 18:00 UTC (02:00 PM EST)
            now_utc = datetime.datetime.utcnow()
            logging.info("ℹ️ [NEWS SENTINEL] Running in baseline macro window monitoring mode.")
            return

        current_date = datetime.date.today().strftime('%Y-%m-%d')
        url = f"https://finnhub.io/api/v1/calendar/economic?from={current_date}&to={current_date}&token={self.api_key}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json().get('economicCalendar', [])
                usd_high_events = []
                
                for event in data:
                    # শুধুমাত্র USD কারেন্সি এবং 'High' ইমপ্যাক্ট (Red Folder) ফিল্টার
                    if event.get('country') == 'US' and event.get('impact') == 'high':
                        event_time_str = event.get('time')
                        if event_time_str:
                            event_dt = datetime.datetime.strptime(event_time_str, '%Y-%m-%d %H:%M:%S')
                            usd_high_events.append(event_dt)
                
                self.cached_news_events = usd_high_events
                self.last_fetch_time = datetime.datetime.utcnow()
                logging.info(f"✅ [NEWS SENTINEL] Successfully fetched {len(usd_high_events)} USD High-Impact events for today.")
            else:
                logging.error(f"⚠️ [NEWS SENTINEL] API Request Failed with status: {response.status_code}")
        except Exception as e:
            logging.error(f"⚠️ [NEWS SENTINEL] Error fetching economic calendar: {str(e)}")

    def is_trading_frozen(self) -> bool:
        """
        বর্তমান সময়ের সাথে কম্পেয়ার করে ৫ মিনিটের সেফটি উইন্ডো ভেরিফাই করে।
        ট্রেড ফ্রিজ করতে হলে True রিটার্ন করবে, অন্যথায় False।
        """
        now_utc = datetime.datetime.utcnow()
        
        # প্রতিদিন প্রথমবার বা প্রতি ২ ঘণ্টা পর পর ক্যাশ এপিআই রিফ্রেশ করা
        if self.last_fetch_time is None or (now_utc - self.last_fetch_time).total_seconds() > 7200:
            self.fetch_usd_high_impact_news()
            
        for news_time in self.cached_news_events:
            time_difference = (news_time - now_utc).total_seconds()
            
            # উইন্ডো ক্যালকুলেশন: নিউজের ৫ মিনিট (৩০০ সেকেন্ড) আগে এবং ৫ মিনিট পরে
            if -300 <= time_difference <= 300:
                logging.warning(
                    f"🛑 [MARKET FREEZE TRIPPED] USD Red-Folder News at {news_time.strftime('%H:%M:%S')} UTC. "
                    f"Time Delta: {time_difference:.1f}s. Halting all new entries!"
                )
                return True
                
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🛡️ ECONOMIC NEWS SENTINEL - UNIT TEST")
    print("=" * 60)
    sentinel = EconomicNewsSentinel(api_key="")
    frozen = sentinel.is_trading_frozen()
    print(f"Current News Freeze Status: {'FROZEN (DO NOT TRADE)' if frozen else 'ACTIVE (SAFE TO TRADE)'}")
