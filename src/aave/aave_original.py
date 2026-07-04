from typing import Dict

# Aave-style borrowing simulator.
class AaveSimulator:

    def __init__(
            self,
            ltv_max: float = 0.65,
            liquidation_threshold: float = 0.70,
            close_factor: float = 0.5,
            liquidation_bonus: float = 0.10,
    ):
        self.ltv_max = ltv_max
        self.liquidation_threshold = liquidation_threshold
        self.close_factor = close_factor
        self.liquidation_bonus = liquidation_bonus

    # Health Factor = (position_value * liquidation_threshold) / loan_amount.
    def calculate_health_factor(self, position_value: float, loan_amount: float) -> float:
        if loan_amount <= 0:
            return float("inf")
        return position_value * self.liquidation_threshold / loan_amount

    # Compute loan amount
    def borrow(self, collateral_value_usd: float) -> float:
        return collateral_value_usd * self.ltv_max

    # Decide whether to liquidate and compute repay / collateral to take.
    def decide_liquidation(self, position_value: float, loan_amount: float) -> Dict[str, float]:
        if loan_amount <= 0:
            return {
                "should_liquidate": False,
                "health_factor": float("inf"),
                "repay_amount": 0.0,
                "collateral_to_take": 0.0,
            }

        hf = self.calculate_health_factor(position_value, loan_amount)

        # Health factor < 1 - liquidating
        if hf < 1.0:
            # compute repay and collateral to take
            repay = loan_amount * self.close_factor
            collateral_taken = repay * (1 + self.liquidation_bonus)
            return {
                "should_liquidate": True,
                "health_factor": hf,
                "repay_amount": repay,
                "collateral_to_take": collateral_taken,
            }
        # Health factor >= 1 - no liquidation
        return {
            "should_liquidate": False,
            "health_factor": hf,
            "repay_amount": 0.0,
            "collateral_to_take": 0.0,
        }