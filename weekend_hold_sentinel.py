"""
WeekendHoldSentinel
Prop Firm Weekend Position & Margin Guardian
Protects accounts from weekend crypto holding disqualifications (e.g. FTMO, FundedNext Friday close rules).
Goat Funded Trader (GFT) mode supports full 24/7 weekend crypto holding.
"""
import datetime
import time
import logging
import os
import urllib.request
import urllib.parse
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_telegram_alert(message: str):
    """Sends immediate high-priority alert to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("⚠️ [TELEGRAM ALERT SKIPPED] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": message}).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, headers={"User-Agent": "WeekendSentinel/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            pass
    except Exception as e:
        logging.error(f"Telegram alert error: {e}")

class WeekendHoldSentinel:
    """
    Monitors MT5 open positions on Friday evenings to prevent weekend holding rule breaches.
    Modes:
      - 'STRICT_PROP_FIRM' (FTMO / FundedNext Standard): All positions must be flattened by Friday 21:45 UTC.
      - 'PERMISSIVE_GFT' (Goat Funded Trader / Swing Plans): 24/7 weekend crypto holding fully allowed.
    """
    def __init__(self, mode: str = "STRICT_PROP_FIRM"):
        self.mode = mode
        self.alert_sent_today = False

    def check_weekend_boundary(self) -> dict:
        now_utc = datetime.datetime.utcnow()
        weekday = now_utc.weekday()  # 4 = Friday, 5 = Saturday, 6 = Sunday
        hour = now_utc.hour
        minute = now_utc.minute

        is_friday_evening = (weekday == 4 and (hour > 21 or (hour == 21 and minute >= 30)))
        is_weekend = (weekday == 5 or weekday == 6)

        if self.mode == "PERMISSIVE_GFT":
            return {
                "action": "HOLD_PERMITTED",
                "reason": "Goat Funded Trader (GFT) supports 500+ pairs 24/7 weekend crypto holding.",
                "should_close": False
            }

        # STRICT_PROP_FIRM MODE (FTMO / FundedNext)
        if is_friday_evening or is_weekend:
            warning_msg = (
                "🚨 [WEEKEND HOLDING SENTINEL - BREACH PREVENTION]\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ Friday Market Close approaching / Weekend Active!\n"
                f"⏰ Current UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🏛️ Mode: {self.mode} (FTMO / FundedNext Rules)\n"
                "🛑 Action: Positions MUST be flattened before Friday 21:45 UTC!\n"
                "━━━━━━━━━━━━━━━━━━━━"
            )
            if not self.alert_sent_today:
                send_telegram_alert(warning_msg)
                self.alert_sent_today = True

            return {
                "action": "FLATTEN_POSITIONS_IMMEDIATELY",
                "reason": "Prop firm rules forbid holding open trades into the weekend rollover.",
                "should_close": True
            }

        # Reset alert flag on Monday
        if weekday == 0:
            self.alert_sent_today = False

        return {
            "action": "NORMAL_TRADING",
            "reason": "Mid-week safe trading window.",
            "should_close": False
        }

if __name__ == "__main__":
    print("=" * 60)
    print("🛡️ WEEKEND HOLD SENTINEL - VERIFICATION")
    print("=" * 60)
    
    # Test 1: Strict Mode
    strict_sentinel = WeekendHoldSentinel(mode="STRICT_PROP_FIRM")
    res1 = strict_sentinel.check_weekend_boundary()
    print("Test 1 (Strict Prop Firm / FTMO Mode):", res1)
    
    # Test 2: Goat Funded Trader Mode
    gft_sentinel = WeekendHoldSentinel(mode="PERMISSIVE_GFT")
    res2 = gft_sentinel.check_weekend_boundary()
    print("Test 2 (Goat Funded Trader 24/7 Crypto Mode):", res2)
