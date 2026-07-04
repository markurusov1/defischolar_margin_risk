import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# Load dataset: each row ≈ one day
# - open_price  → P1 (price at start of day)
# - close_price → P2 (price at end of day)
# - price_change → realized % change over the day
# - average_health_factor → realized health factor at/near end of day
df = pd.read_csv('../output/run_20260111_122829/liquidation_timeseries.csv', parse_dates=['date'])

# Fit regression once: health_factor ≈ f(price_change)
# This gives a baseline linear projection we can adjust with IL
X = df['price_change'].values.reshape(-1, 1)
y = df['average_health_factor'].values
model = LinearRegression()
model.fit(X, y)

# Discrete shock levels (% from current price) for stress testing
# Inspired by SEC Portfolio Margin valuation points
shocks = np.array([-15, -12, -9, -6, -3, 0, 3, 6, 9, 12, 15])

# Uniswap v3 token amount calculation (concentrated liquidity math)
def get_amounts(P, pa, pb, L):
    """Returns amount0 and amount1 in range [pa, pb] at price P."""
    if P <= 0 or pa <= 0 or pb <= 0 or pa >= pb:
        return 0, 0
    sqrtP = np.sqrt(P)
    sqrta = np.sqrt(pa)
    sqrtb = np.sqrt(pb)
    if P < pa:
        amount0 = L * (1/sqrta - 1/sqrtb)
        amount1 = 0
    elif P > pb:
        amount0 = 0
        amount1 = L * (sqrtb - sqrta)
    else:
        amount0 = L * (1/sqrtP - 1/sqrtb)
        amount1 = L * (sqrtP - sqrta)
    return amount0, amount1

# Impermanent loss calculator for narrow-range v3 position
# Returns IL as fraction (negative = loss)
def compute_il(P_current, P_shocked, pa_factor=0.9, pb_factor=1.1, initial_L=10000):
    pa = P_current * pa_factor
    pb = P_current * pb_factor
    amount0_init, amount1_init = get_amounts(P_current, pa, pb, initial_L)
    initial_value = amount0_init + amount1_init * P_current
    if initial_value == 0:
        return 0
    scale = 100 / initial_value  # Normalize to $100 initial value
    amount0_init *= scale
    amount1_init *= scale
    amount0_shock, amount1_shock = get_amounts(P_shocked, pa, pb, initial_L * scale)
    pool_value = amount0_shock + amount1_shock * P_shocked
    hold_value = amount0_init + amount1_init * P_shocked
    if hold_value == 0:
        return 0
    return (pool_value - hold_value) / hold_value

# Simulate TradFi-style dynamic margin / liquidation checks
tradfi_liquidations = []

# Extra cushion on worst-case health
# TODO - research the buffer
buffer = 0.1

# loop over the dates
for i in range(len(df)):
    # ── Step 1: Set limits / threshold at initial price (P1 = open_price)
    initial_price = df['open_price'].iloc[i]
    projected_healths = []

    #Calculate the projected health factor for each initial price
    for shock_pct in shocks:
        P_shocked = initial_price * (1 + shock_pct / 100)
        il = compute_il(initial_price, P_shocked)               # IL under this hypothetical shock
        projected_health = model.predict([[shock_pct]])[0] + il
        projected_healths.append(projected_health)

    #take the worst of all outcomes
    worst_projected_h = min(projected_healths)
    # Dynamic margin requirement proxy.
    # TODO could be more sophisticated.
    initial_threshold = worst_projected_h + buffer

    # ── Step 2: Check against a realized outcome after price change to P2
    actual_h = df['average_health_factor'].iloc[i]   # Realized health after move to P2
    #compare the actual health factor to the worst case projection
    triggered = actual_h < initial_threshold

    print(f"Date: {df['date'].iloc[i]}, Open: {initial_price:.2f}, Close: {df['close_price'].iloc[i]:.2f}, "
          f"Actual H: {actual_h:.4f}, Worst Projected H: {worst_projected_h:.4f}, Initial Threshold: "
          f"{initial_threshold:.4f} | Triggered: {triggered}")

    # Decision: trigger liquidation if realized health violated the initial day's stress cushion
    # (We could add "and actual_h < worst_h_p2" for stricter double-check, but keeping it simple here)
    tradfi_liquidations.append(1 if triggered else 0)

# Attach results and compute summary
df['tradfi_liquidations'] = tradfi_liquidations
df['fixed_liquidations'] = df['number_of_liquidations']

fixed_count = (df['fixed_liquidations'] > 0).sum()
tradfi_count = (df['tradfi_liquidations'] > 0).sum()
reduction_pct = ((fixed_count - tradfi_count) / fixed_count * 100) if fixed_count > 0 else 0

print(f'Fixed LTV Liquidations: {fixed_count}')
print(f'TradFi Stress-Test Liquidations: {tradfi_count}')
print(f'Reduction: {reduction_pct:.2f}%')