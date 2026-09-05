"""
SpotTriangularArbitrageEngine
Asynchronous 100% Halal Spot Triangular Arbitrage Engine (Zero Margin, Zero Riba)
Calculates real-time triangular cross-rates with 3-leg taker-fee deduction:
Leg 1: Asset A -> Asset B (e.g. USDT -> BTC)
Leg 2: Asset B -> Asset C (e.g. BTC -> ETH)
Leg 3: Asset C -> Asset A (e.g. ETH -> USDT)
"""

import asyncio
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class SpotTriangularArbitrageEngine:
    def __init__(self, asset_a: str = "USDT", asset_b: str = "BTC", asset_c: str = "ETH", trading_size_a: float = 1000.0, taker_fee_rate: float = 0.001):
        self.asset_a = asset_a  # Base Currency (e.g., USDT)
        self.asset_b = asset_b  # Intermediate Currency (e.g., BTC)
        self.asset_c = asset_c  # Target Currency (e.g., ETH)
        self.trading_size_a = float(trading_size_a)
        self.taker_fee_rate = taker_fee_rate  # 0.1% standard taker fee per leg
        self.is_running = True

    def calculate_triangular_pnl(self, ask_ab: float, ask_cb: float, bid_ca: float) -> Dict[str, Any]:
        """
        Computes the net PnL of 3-leg spot conversion including compounded exchange fees:
        Step 1: Buy Asset B using Asset A capital -> qty_b = size_a / ask_ab
        Step 2: Buy Asset C using Asset B balance -> qty_c = qty_b / ask_cb
        Step 3: Sell Asset C to receive Asset A -> final_qty_a = qty_c * bid_ca
        """
        # Step 1
        qty_b = self.trading_size_a / ask_ab
        # Step 2
        qty_c = qty_b / ask_cb
        # Step 3
        gross_final_a = qty_c * bid_ca
        
        # 3 legs fee compounding: (1 - fee)^3
        net_multiplier = (1.0 - self.taker_fee_rate) ** 3
        net_final_a = gross_final_a * net_multiplier
        net_profit = net_final_a - self.trading_size_a
        roi_pct = (net_profit / self.trading_size_a) * 100.0

        return {
            "gross_return": round(gross_final_a, 4),
            "net_return": round(net_final_a, 4),
            "net_profit": round(net_profit, 4),
            "roi_pct": round(roi_pct, 4),
            "is_profitable": net_profit > 0.0
        }

if __name__ == "__main__":
    print("=" * 60)
    print("🔺 SHARIAH SPOT TRIANGULAR ARBITRAGE ENGINE - TEST")
    print("=" * 60)
    engine = SpotTriangularArbitrageEngine(asset_a="USDT", asset_b="BTC", asset_c="ETH", trading_size_a=1000.0)
    
    # Test case 1: Standard market rates (No Arb)
    res1 = engine.calculate_triangular_pnl(ask_ab=60000.0, ask_cb=0.040, bid_ca=2395.0)
    print("Test 1 (Normal Efficient Market):", res1)
    
    # Test case 2: Momentary Discrepancy (Arb Opportunity)
    res2 = engine.calculate_triangular_pnl(ask_ab=59800.0, ask_cb=0.039, bid_ca=2410.0)
    print("Test 2 (Arbitrage Anomaly Detected):", res2)
