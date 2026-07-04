# Quick test to verify the simulator works

print("Starting test...")

from simulator import run_simulation

print("Running simulation with 10 positions...")
result = run_simulation(n_positions=10)

summary = result['summary']
timeseries = result['timeseries']

print("\n===== RESULTS =====")
print(f"Total dates simulated: {summary['total_dates']}")
print(f"Total positions: {summary['total_positions']}")
print(f"Total liquidation events: {summary['total_liquidations_all']}")
print(f"Unique positions ever liquidated: {summary['unique_positions_ever_liquidated']}")
print(f"Average health factor: {summary['avg_health_factor_all']:.4f}")

print("\nFirst 5 dates:")
for i, row in enumerate(timeseries[:5]):
    print(f"  {row['date']} | price={row['price']:.2f} | liq={row['total_liquidations']}")

print("\nLast 5 dates:")
for i, row in enumerate(timeseries[-5:]):
    print(f"  {row['date']} | price={row['price']:.2f} | liq={row['total_liquidations']}")

print("\nTest complete!")

