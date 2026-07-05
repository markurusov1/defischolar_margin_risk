import random
from typing import List

from il_v3 import UniswapV3Position

# ────────────────────────────────────────────────
# Simulation parameters (module-level defaults)
# ────────────────────────────────────────────────
N_POSITIONS = 500
MIN_FUNDING = 6000
MAX_FUNDING = 10000
MIN_RANGE_WIDTH = 0.10  # ±10%
MAX_RANGE_WIDTH = 0.60  # ±60%
INITIAL_ETH_PRICE = 2500.0  # Realistic mid-Jan 2026 assumption

__all__ = ["create_positions", "N_POSITIONS", "MIN_FUNDING", "MAX_FUNDING", "INITIAL_ETH_PRICE"]


def create_positions(
        n_positions: int = N_POSITIONS,
        min_funding: float = MIN_FUNDING,
        max_funding: float = MAX_FUNDING,
        min_range_width: float = MIN_RANGE_WIDTH,
        max_range_width: float = MAX_RANGE_WIDTH,
        initial_eth_price: float = INITIAL_ETH_PRICE,
        id_prefix: str = "id#",
) -> List[UniswapV3Position]:
    """
    Create a list of UniswapV3Position instances.

    Returns:
        List of positions created with positional args:
        UniswapV3Position(id, eth_max, usdc_max, range_width)
    """
    results: List[UniswapV3Position] = []

    for i in range(n_positions):
        total_funding = random.uniform(min_funding, max_funding)

        # Random split between ETH and USDC amounts
        eth_ratio = random.uniform(0.3, 0.7)  # 30-70% in ETH value terms
        eth_max_value = total_funding * eth_ratio

        usdc_max = total_funding * (1 - eth_ratio)
        eth_max = eth_max_value / initial_eth_price

        # concentrated liquidity range
        range_width = random.uniform(min_range_width, max_range_width)

        # create the position
        pos = UniswapV3Position(id_prefix + f"{i}", eth_max, usdc_max, range_width)

        # add position to the list
        results.append(pos)

    return results


if __name__ == "__main__":
    positions = create_positions(n_positions=10)
