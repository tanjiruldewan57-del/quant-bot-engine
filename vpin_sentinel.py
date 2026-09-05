"""
VPINSentinel (Volume-Synchronized Probability of Informed Trading)
Detects toxic order flow imbalances, adverse selection, and impending flash crashes.
Operates on a Volume Clock rather than a Calendar Clock:
1. Volume Bucketing: Divides trade stream into buckets of fixed volume V
2. Bulk Volume Classification (BVC): V_tau^B = V * Phi(Delta_P / sigma_P)
3. Rolling VPIN over n=50 buckets: VPIN = (1/n) * sum(|V_tau^B - V_tau^S| / V)
4. Defensively halts aggressive sniper buying when VPIN >= 0.70
"""

import math
import numpy as np
import logging
from collections import deque
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def standard_normal_cdf(x: float) -> float:
    """Cumulative distribution function for standard normal distribution."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

class VPINSentinel:
    def __init__(self, bucket_size_v: float = 1000.0, rolling_window_n: int = 50, toxic_threshold: float = 0.70):
        self.bucket_size_v = bucket_size_v
        self.rolling_window_n = rolling_window_n
        self.toxic_threshold = toxic_threshold
        
        self.current_bucket_vol = 0.0
        self.bucket_start_price = None
        self.last_price = None
        
        self.price_deltas = deque(maxlen=200)
        self.imbalances = deque(maxlen=rolling_window_n)
        self.current_vpin = 0.0

    def update_tick(self, price: float, volume: float) -> dict:
        """
        Ingests tick/trade update and progresses the volume clock.
        :param price: Current asset traded price
        :param volume: Traded volume in this tick
        """
        if self.bucket_start_price is None:
            self.bucket_start_price = price
            self.last_price = price

        self.current_bucket_vol += volume
        self.last_price = price

        # Check if the volume bucket V has filled
        if self.current_bucket_vol >= self.bucket_size_v:
            delta_p = self.last_price - self.bucket_start_price
            self.price_deltas.append(delta_p)
            
            # Historical volatility of price deltas
            sigma_p = np.std(self.price_deltas) if len(self.price_deltas) > 5 else 0.01
            if sigma_p <= 1e-8:
                sigma_p = 0.01
            
            # Step 2: Bulk Volume Classification (BVC)
            z_score = delta_p / sigma_p
            buy_fraction = standard_normal_cdf(z_score)
            v_buy = self.bucket_size_v * buy_fraction
            v_sell = self.bucket_size_v - v_buy
            
            # Step 3: Raw Bucket Imbalance
            bucket_imbalance = abs(v_buy - v_sell) / self.bucket_size_v
            self.imbalances.append(bucket_imbalance)
            
            # Step 4: Rolling VPIN over n buckets
            if len(self.imbalances) > 0:
                self.current_vpin = sum(self.imbalances) / len(self.imbalances)
            
            # Reset bucket
            self.current_bucket_vol = 0.0
            self.bucket_start_price = self.last_price

        # Evaluate Toxicity Regime
        is_toxic = self.current_vpin >= self.toxic_threshold
        regime = "TOXIC_INFORMED_FLOW (FLASH CRASH RISK)" if is_toxic else (
            "TRENDING_FLOW" if self.current_vpin >= 0.40 else "BALANCED_UNINFORMED_FLOW"
        )
        
        return {
            "vpin": round(self.current_vpin, 4),
            "is_toxic": is_toxic,
            "regime": regime,
            "should_halt_buying": is_toxic
        }

if __name__ == "__main__":
    print("=" * 60)
    print("🌊 VPIN SENTINEL (TOXIC ORDER FLOW SENSOR) - TEST RUN")
    print("=" * 60)
    
    sentinel = VPINSentinel(bucket_size_v=100.0, rolling_window_n=20, toxic_threshold=0.70)
    
    # Simulate normal balanced trading
    price = 2500.0
    for _ in range(50):
        price += np.random.normal(0, 0.5)
        res = sentinel.update_tick(price=price, volume=25.0)
    print("Balanced Market State:", res)
    
    # Simulate sudden toxic liquidation cascade (one-sided selling)
    for _ in range(30):
        price -= 5.0  # sharp drop
        res = sentinel.update_tick(price=price, volume=120.0)
    print("Liquidating Cascade State:", res)
