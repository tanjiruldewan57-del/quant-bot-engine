"""
ShariahSpotKellyRiskEngine
Grossman-Zhou Capital Floor & Conformal-Scaled Fractional Kelly Position Sizing Engine
Strictly Shariah-Compliant (100% Spot, Zero Margin, Zero Riba)
"""
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ShariahSpotKellyRiskEngine:
    """
    Grossman-Zhou Capital Floor এবং Conformal-Scaled Fractional Kelly-ভিত্তিক 
    শরীয়াহ-সম্মত স্পট পজিশন সাইজিং ইঞ্জিন.
    """
    def __init__(self, starting_capital: float = 100000.0, max_drawdown_pct: float = 0.10, fractional_multiplier: float = 0.25):
        self.hwm = starting_capital  # High-Water Mark (HWM) ট্র্যাকিং
        self.max_drawdown_pct = max_drawdown_pct  # সর্বোচ্চ ট্রেইলিং ড্রডাউন (যেমন: ১০% বা প্রপ ফার্ম ৫%)
        self.fractional_multiplier = fractional_multiplier  # কেলি ফ্র্যাকশন স্কেলার (Quarter-Kelly = 0.25)
        self.min_allocation_usd = 10.0  # এক্সচেঞ্জ মিনিমাম অর্ডার সাইজ থ্রেশহোল্ড
        
    def update_high_water_mark(self, current_equity: float) -> float:
        """অ্যাকাউন্ট ইকুইটি বাড়লে রান-টাইমে হাই-ওয়াটার মার্ক আপডেট করে."""
        if current_equity > self.hwm:
            logging.info(f"📈 [HWM UPDATED] ${self.hwm:,.2f} -> ${current_equity:,.2f}")
            self.hwm = current_equity
        return self.hwm

    def calculate_active_cushion(self, current_equity: float) -> float:
        """ক্যাপিটাল ফ্লোর বজায় রাখতে একটিভ কুশন (Active Cushion) হিসাব করে."""
        capital_floor = self.hwm * (1.0 - self.max_drawdown_pct)  # Grossman-Zhou Floor
        active_cushion = max(0.0, current_equity - capital_floor)
        return active_cushion

    def calculate_kelly_fraction(self, win_rate: float, payoff_ratio: float) -> float:
        """
        স্ট্যান্ডার্ড কেলি ফর্মুলার সাহায্যে রিস্ক ফ্র্যাকশন হিসাব করে:
        f* = (p * b - q) / b , যেখানে b = Payoff Ratio, p = Win Rate, q = 1 - p.
        """
        p = win_rate
        q = 1.0 - p
        b = payoff_ratio
        
        if b <= 0:
            return 0.0
            
        unconstrained_kelly = (p * b - q) / b
        
        # কেবল পজিটিভ এজ (Positive Edge) থাকলে কেলি সাইজিং এলাও করা হবে
        return max(0.0, unconstrained_kelly)

    def compute_spot_allocation(self, current_equity: float, win_rate: float, 
                                payoff_ratio: float, asset_price: float) -> dict:
        """
        স্পট এন্ট্রির জন্য ড্রডাউন-মডুলেটেড এবং স্কেলড পজিশন সাইজ (USD & Lot) হিসাব করে.
        """
        # ১. রান-টাইম এইচডব্লিউএম ট্র্যাকিং ও আপডেট
        self.update_high_water_mark(current_equity)
        
        # ২. একটিভ রিস্ক ক্যাপিটাল কুশন হিসাব
        cushion = self.calculate_active_cushion(current_equity)
        
        # ৩. কেলি অনুপাত এবং কোয়ার্টার-কেলি স্কেলিং
        raw_kelly = self.calculate_kelly_fraction(win_rate, payoff_ratio)
        scaled_kelly = raw_kelly * self.fractional_multiplier  # f_scaled = c * f*
        
        # ৪. স্পট বাজেট নির্ধারণ (Grossman-Zhou Risk Budgeting)
        allocated_capital_usd = scaled_kelly * cushion
        
        # ৫. নো-লেভারেজ স্পট বাউন্ডারি চেক (ক্যাশের চেয়ে বেশি কেনা যাবে না)
        final_allocation_usd = min(current_equity, allocated_capital_usd)
        
        # ৬. লট সাইজ কনভার্সন
        lot_size = final_allocation_usd / asset_price if asset_price > 0 else 0.0
        
        execution_allowed = final_allocation_usd >= self.min_allocation_usd and cushion > 0
        
        return {
            "current_equity": current_equity,
            "high_water_mark": self.hwm,
            "capital_floor": self.hwm * (1.0 - self.max_drawdown_pct),
            "active_cushion": cushion,
            "raw_kelly_fraction": round(raw_kelly, 4),
            "scaled_kelly_fraction": round(scaled_kelly, 4),
            "final_allocation_usd": round(final_allocation_usd, 2) if execution_allowed else 0.0,
            "position_lot_size": round(lot_size, 4) if execution_allowed else 0.0,
            "status": "EXECUTION_ALLOWED" if execution_allowed else "HALT_TRADING_FLOOR_BREACH"
        }

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 SHARIAH SPOT KELLY RISK ENGINE - UNIT VERIFICATION")
    print("=" * 60)
    engine = ShariahSpotKellyRiskEngine(starting_capital=100000.0, max_drawdown_pct=0.10, fractional_multiplier=0.25)
    
    # টেস্ট কেস ১: সাধারণ একাউন্ট স্টেট (উইন রেট ৮৫.৭%, পে-অফ রেশিও ১:১.২)
    s1 = engine.compute_spot_allocation(current_equity=100000.0, win_rate=0.857, payoff_ratio=1.2, asset_price=2450.0)
    print("\n[Scenario 1: Normal Institutional Balance ($100k)]")
    for k, v in s1.items():
        print(f"  • {k}: {v}")
        
    # টেস্ট কেস ২: ড্রডাউন স্ট্রেস টেস্ট (ইকুইটি কমে $92k হয়েছে)
    s2 = engine.compute_spot_allocation(current_equity=92000.0, win_rate=0.857, payoff_ratio=1.2, asset_price=2450.0)
    print("\n[Scenario 2: Under Drawdown Pressure ($92k Equity)]")
    for k, v in s2.items():
        print(f"  • {k}: {v}")
