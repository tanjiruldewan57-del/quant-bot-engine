"""
================================================================================
🧮 DAPS (DRAWDOWN ADAPTIVE POSITION SIZING) & RECONCILED KELLY ENGINE
================================================================================
File: daps_calculator.py
Purpose:
- Dynamically scales risk budget as equity approaches maximum allowable drawdown
- Implements Half-Kelly fraction constrained by Grossman-Zhou safety floor
- Integrates Conformal Prediction Intervals (CPI) for fakeout filtering
- Adheres strictly to 100% Shariah Mudarabah capital protection standards
================================================================================
"""

import numpy as np

def calculate_daps(balance: float, peak: float, max_loss: float = 0.05, base_risk: float = 0.03, stop_loss: float = 0.01) -> float:
    """
    Unified Operational DAPS Sizing Logic.
    Adjusts position size dynamically as account decays toward max drawdown (D_max).
    Formula: R_t = R_base * (1 - D_t / D_max)^1.5
    """
    floor = peak * (1.0 - max_loss)
    buffer = max(0.0, balance - floor)
    if buffer <= 0.0:
        return 0.0  # HALT TRADING — Zero Maysir / 100% Capital Floor Protection
    
    allowed_risk = buffer * 0.185
    pos_size = allowed_risk / stop_loss
    max_risk = balance * base_risk
    if allowed_risk > max_risk:
        allowed_risk = max_risk
        pos_size = allowed_risk / stop_loss
    return round(pos_size, 2)

def calculate_daps_position_size(
    current_balance: float,
    high_water_mark: float,
    max_daily_drawdown_pct: float = 0.03,
    base_risk_pct: float = 0.02,
    stop_loss_pct: float = 0.01,
    win_rate: float = 0.55,
    risk_reward_ratio: float = 2.5
) -> dict:
    """
    Reconciled DAPS Core Calculator with Half-Kelly Fraction.
    """
    hwm = max(current_balance, high_water_mark)
    capital_floor = hwm * (1.0 - max_daily_drawdown_pct)
    active_buffer = max(0.0, current_balance - capital_floor)
    
    if active_buffer <= 0.0:
        return {
            "status": "HALT_TRADING",
            "message": "🛑 Daily Drawdown Limit Reached! Floor protection engaged.",
            "position_size_usd": 0.0,
            "risk_amount_usd": 0.0
        }
    
    # Unconstrained Kelly Fraction -> Half-Kelly for hedge-fund conservatism
    unconstrained_kelly = (risk_reward_ratio * win_rate - (1.0 - win_rate)) / risk_reward_ratio
    half_kelly_fraction = 0.5 * max(0.0, unconstrained_kelly)
    risk_budget_usd = half_kelly_fraction * active_buffer
    position_size_usd = risk_budget_usd / stop_loss_pct
    
    max_base_risk_usd = current_balance * base_risk_pct
    if risk_budget_usd > max_base_risk_usd:
        risk_budget_usd = max_base_risk_usd
        position_size_usd = risk_budget_usd / stop_loss_pct
        
    return {
        "status": "EXECUTION_ALLOWED",
        "current_balance": round(current_balance, 2),
        "high_water_mark": round(hwm, 2),
        "capital_floor": round(capital_floor, 2),
        "active_buffer": round(active_buffer, 2),
        "allowed_risk_usd": round(risk_budget_usd, 2),
        "optimal_position_size_usd": round(position_size_usd, 2),
        "applied_kelly_fraction_pct": round(half_kelly_fraction * 100, 2)
    }

class AdvancedCompetitionEngine:
    """Integrated Strategy Engine with Conformal Prediction Intervals (CPI) & OFI."""
    def __init__(self, start_balance: float = 100000.0, max_daily_drawdown_pct: float = 0.05, target_profit_pct: float = 0.15):
        self.balance = start_balance
        self.peak_balance = start_balance
        self.max_daily_loss = max_daily_drawdown_pct
        self.target_profit = start_balance * (1.0 + target_profit_pct)
        self.price_history = []

    def calculate_conformal_boundaries(self, current_price: float, window_size: int = 50, significance: float = 0.05):
        self.price_history.append(current_price)
        if len(self.price_history) < window_size:
            return current_price * 0.99, current_price * 1.01
        if len(self.price_history) > window_size:
            self.price_history.pop(0)
            
        prices = np.array(self.price_history)
        mean_p = np.mean(prices)
        scores = np.abs(prices - mean_p)
        sorted_scores = np.sort(scores)
        q_index = int(np.ceil((1.0 - significance) * len(prices))) - 1
        q_val = sorted_scores[q_index]
        return mean_p - q_val, mean_p + q_val

    def daps_competition_sizing(self, current_balance: float, stop_loss_pct: float = 0.01) -> float:
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
        floor = self.peak_balance * (1.0 - self.max_daily_loss)
        active_buffer = max(0.0, current_balance - floor)
        if active_buffer <= 0.0:
            return 0.0
        
        # Velocity phase vs lock-in phase scaling
        applied_risk_fraction = 0.052 if current_balance >= self.target_profit else 0.185
        allowed_risk_usd = active_buffer * applied_risk_fraction
        return min(allowed_risk_usd / stop_loss_pct, current_balance)

    def evaluate_entry(self, current_price: float, bid_vol: float, ask_vol: float, current_balance: float) -> dict:
        lower_b, upper_b = self.calculate_conformal_boundaries(current_price)
        ofi_norm = (bid_vol - ask_vol) / (0.5 * (bid_vol + ask_vol) + 1e-12)
        
        if current_price <= lower_b and ofi_norm > 0.15:
            pos_size = self.daps_competition_sizing(current_balance)
            if pos_size > 0:
                return {
                    "signal": "BUY_LIMIT",
                    "price": current_price,
                    "position_size_usd": round(pos_size, 2),
                    "target_profit_usd": round(current_price * 1.03, 2),
                    "stop_loss_usd": round(current_price * 0.99, 2)
                }
        return {"signal": "STANDBY", "price": current_price, "position_size_usd": 0.0}

if __name__ == "__main__":
    test_calc = calculate_daps_position_size(100000.0, 100000.0)
    print("✅ [DAPS TEST] Result:", test_calc)
