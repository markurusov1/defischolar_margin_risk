import math

def calculate_impermanent_loss(price_ratio):
    """
    Calculate impermanent loss using the standard approximation formula
    for a balanced (50/50 value) Uniswap v2-style or full-range v3 position.

    IL = 2 * sqrt(r) / (1 + r) - 1
    where r = new_price / old_price

    Returns IL as a decimal (negative = loss).
    """
    if price_ratio <= 0:
        raise ValueError("Price ratio must be positive")
    return (2 * math.sqrt(price_ratio) / (1 + price_ratio)) - 1

# -----------------------------
# Example Simulation
# -----------------------------

# LP deposits into ETH/USDC pool
initial_eth_deposit = 3000.0    # Amount of ETH deposited
initial_usdc_deposit = 2000.0   # Amount of USDC deposited

# Current price implied by the deposit ratios (balanced position)
# Price = USDC per ETH
initial_price = initial_usdc_deposit / initial_eth_deposit
print(f"Initial price (USDC per ETH): {initial_price:.4f}")

# Initial total value of the position (in USDC)
initial_value = initial_eth_deposit * initial_price + initial_usdc_deposit
print(f"Initial LP position value: {initial_value:.2f} USDC")

# Constant product K (for Uniswap v2 / full-range approximation)
K = initial_eth_deposit * initial_usdc_deposit

# ETH price drops by 10% → new price ratio r = 0.9
price_drop = 0.10
r = 1 - price_drop
new_price = initial_price * r
print(f"\nAfter {price_drop*100:.0f}% ETH price drop:")
print(f"New price (USDC per ETH): {new_price:.4f}")
print(f"Price ratio r = {r:.2f}")

# New pool reserves after arbitrage adjusts to the new price
new_eth_reserve = math.sqrt(K / new_price)
new_usdc_reserve = math.sqrt(K * new_price)

print(f"New pool reserves: {new_eth_reserve:.2f} ETH and {new_usdc_reserve:.2f} USDC")

# Value of LP position if staying in the pool (100% share for simplicity)
pool_value_new = new_eth_reserve * new_price + new_usdc_reserve
print(f"Pool position value at new price: {pool_value_new:.2f} USDC")

# Value if LP had simply held the original tokens (no pool)
hold_value_new = initial_eth_deposit * new_price + initial_usdc_deposit
print(f"Hold strategy value at new price: {hold_value_new:.2f} USDC")

# Impermanent Loss (detailed calculation)
il_detailed = (pool_value_new / hold_value_new) - 1
print(f"\nImpermanent Loss (detailed): {il_detailed:.4f} or {il_detailed*100:.2f}%")

# Impermanent Loss using the closed-form formula (should match exactly)
il_formula = calculate_impermanent_loss(r)
print(f"Impermanent Loss (formula): {il_formula:.4f} or {il_formula*100:.2f}%")