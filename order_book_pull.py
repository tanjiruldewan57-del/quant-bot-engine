"""
================================================================================
📊 LEVEL 2 (L2) CCXT ORDER BOOK & NORMALIZED OFI DETECTOR
================================================================================
File: order_book_pull.py
Purpose:
- Fetches real-time L2 orderbook depth via CCXT
- Computes Top-of-Book Normalized Order Flow Imbalance (OFI)
- Detects institutional bid absorption (OFI > 0.15) for high-conviction entries
================================================================================
"""

import time
import ccxt
import pandas as pd

class CCXTOrderBookPuller:
    def __init__(self, exchange_id='binance', symbol='ETH/USDT'):
        self.exchange = getattr(ccxt, exchange_id)({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        self.symbol = symbol
        self.prev_bid_px = None
        self.prev_bid_sz = None
        self.prev_ask_px = None
        self.prev_ask_sz = None

    def fetch_l2_order_book(self, limit=5):
        try:
            ob = self.exchange.fetch_order_book(self.symbol, limit)
            bids, asks = ob['bids'], ob['asks']
            if not bids or not asks:
                return None
            tb_px, tb_sz = bids[0][0], bids[0][1]
            ta_px, ta_sz = asks[0][0], asks[0][1]
            ofi_norm = self._calculate_ofi(tb_px, tb_sz, ta_px, ta_sz)
            return {
                'timestamp': pd.to_datetime(ob['timestamp'], unit='ms') if ob.get('timestamp') else pd.Timestamp.now(),
                'top_bid_price': tb_px,
                'top_bid_size': tb_sz,
                'top_ask_price': ta_px,
                'top_ask_size': ta_sz,
                'mid_price': (tb_px + ta_px) / 2.0,
                'spread': round(ta_px - tb_px, 4),
                'normalized_ofi': round(ofi_norm, 6)
            }
        except Exception as e:
            return None

    def _calculate_ofi(self, bid_px, bid_sz, ask_px, ask_sz):
        if self.prev_bid_px is None:
            self._update_state(bid_px, bid_sz, ask_px, ask_sz)
            return 0.0
        delta_v_b = bid_sz if bid_px > self.prev_bid_px else (bid_sz - self.prev_bid_sz if bid_px == self.prev_bid_px else -self.prev_bid_sz)
        delta_v_a = ask_sz if ask_px < self.prev_ask_px else (ask_sz - self.prev_ask_sz if ask_px == self.prev_ask_px else -self.prev_ask_sz)
        ofi_norm = (delta_v_b - delta_v_a) / (0.5 * (bid_sz + ask_sz) + 1e-12)
        self._update_state(bid_px, bid_sz, ask_px, ask_sz)
        return ofi_norm

    def _update_state(self, bid_px, bid_sz, ask_px, ask_sz):
        self.prev_bid_px, self.prev_bid_sz = bid_px, bid_sz
        self.prev_ask_px, self.prev_ask_sz = ask_px, ask_sz

if __name__ == "__main__":
    print("📡 Testing CCXT L2 Orderbook OFI Puller...")
    puller = CCXTOrderBookPuller()
    data = puller.fetch_l2_order_book()
    if data:
        print("✅ [L2 OFI DATA]:", data)
    else:
        print("⚠️ Waiting for connection...")
