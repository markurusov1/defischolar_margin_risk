import pandas as pd
import matplotlib.pyplot as plt

# Read the DeFi timeseries
defi_df = pd.read_csv('../output/paper_data/liquidation_timeseries.csv')
defi_df['date'] = pd.to_datetime(defi_df['date'])
defi_df.set_index('date', inplace=True)

# Read the TradFi timeseries
tradfi_df = pd.read_csv('../output/paper_data/hybrid_adjusted_timeseries.csv')
tradfi_df['date'] = pd.to_datetime(tradfi_df['date'])
tradfi_df.set_index('date', inplace=True)

# Ensure both dataframes cover the same date range
common_dates = defi_df.index.intersection(tradfi_df.index)
defi_df = defi_df.loc[common_dates]
tradfi_df = tradfi_df.loc[common_dates]

# Chart 1: Close Price Over Time (should be similar for both)
plt.figure(figsize=(12, 6))
plt.plot(defi_df.index, defi_df['close_price'], label='DeFi Close Price')
plt.plot(tradfi_df.index, tradfi_df['close_price'], label='TradFi Close Price', linestyle='--')
plt.title('Close Price Over Time: DeFi vs TradFi')
plt.xlabel('Date')
plt.ylabel('Close Price')
plt.legend()
plt.grid(True)
plt.savefig('../output/paper_data/close_price_comparison.png')
plt.close()

# Chart 2: Price Change Percentage Over Time
plt.figure(figsize=(12, 6))
plt.plot(defi_df.index, defi_df['price_change'], label='DeFi Price Change %')
plt.plot(tradfi_df.index, tradfi_df['price_change_pct'], label='TradFi Price Change %', linestyle='--')
plt.title('Price Change Percentage Over Time: DeFi vs TradFi')
plt.xlabel('Date')
plt.ylabel('Price Change %')
plt.legend()
plt.grid(True)
plt.savefig('../output/paper_data/price_change_comparison.png')
plt.close()

# Chart 3: Number of Liquidations Over Time
plt.figure(figsize=(12, 6))
plt.plot(defi_df.index, defi_df['number_of_liquidations'], label='DeFi Liquidations')
plt.plot(tradfi_df.index, tradfi_df['liquidations_tradfi_adjusted'], label='TradFi Adjusted Liquidations', linestyle='--')
plt.title('Liquidations Over Time: DeFi vs TradFi')
plt.xlabel('Date')
plt.ylabel('Number of Liquidations')
plt.legend()
plt.grid(True)
plt.savefig('../output/paper_data/liquidations_comparison.png')
plt.close()

# Chart 4: Average Health Factor Over Time
plt.figure(figsize=(12, 6))
plt.plot(defi_df.index, defi_df['average_health_factor'], label='DeFi Avg Health Factor')
plt.plot(tradfi_df.index, tradfi_df['avg_health_factor'], label='TradFi Avg Health Factor', linestyle='--')
plt.title('Average Health Factor Over Time: DeFi vs TradFi')
plt.xlabel('Date')
plt.ylabel('Average Health Factor')
plt.legend()
plt.grid(True)
plt.savefig('../output/paper_data/health_factor_comparison.png')
plt.close()

# Chart 5: Cumulative Liquidations
defi_cum_liquidations = defi_df['number_of_liquidations'].cumsum()
tradfi_cum_liquidations = tradfi_df['liquidations_tradfi_adjusted'].cumsum()

plt.figure(figsize=(12, 6))
plt.plot(defi_cum_liquidations.index, defi_cum_liquidations, label='DeFi Cumulative Liquidations')
plt.plot(tradfi_cum_liquidations.index, tradfi_cum_liquidations, label='TradFi Cumulative Liquidations', linestyle='--')
plt.title('Cumulative Liquidations Over Time: DeFi vs TradFi')
plt.xlabel('Date')
plt.ylabel('Cumulative Liquidations')
plt.legend()
plt.grid(True)
plt.savefig('../output/paper_data/cumulative_liquidations.png')
plt.close()

# Additional Stats for the Paper
total_defi_liquidations = defi_df['number_of_liquidations'].sum()
total_tradfi_liquidations = tradfi_df['liquidations_tradfi_adjusted'].sum()
liquidation_reduction_pct = (1 - (total_tradfi_liquidations / total_defi_liquidations)) * 100 if total_defi_liquidations != 0 else 0

days_with_defi_liq = (defi_df['number_of_liquidations'] > 0).sum()
days_with_tradfi_liq = (tradfi_df['liquidations_tradfi_adjusted'] > 0).sum()

stats = {
    'Total DeFi Liquidations': total_defi_liquidations,
    'Total TradFi Liquidations': total_tradfi_liquidations,
    'Liquidation Reduction %': liquidation_reduction_pct,
    'Days with DeFi Liquidations': days_with_defi_liq,
    'Days with TradFi Liquidations': days_with_tradfi_liq
}

print(stats)

# Write stats to file
with open('../output/paper_data/summary.txt', 'w') as f:
    for key, value in stats.items():
        f.write(f'{key}: {value}\n')

# TradFi Specific Charts
# Chart 6: Average Effective LTV Over Time (TradFi only)
plt.figure(figsize=(12, 6))
plt.plot(tradfi_df.index, tradfi_df['avg_effective_ltv'], label='TradFi Avg Effective LTV')
plt.title('Average Effective LTV Over Time (TradFi)')
plt.xlabel('Date')
plt.ylabel('Avg Effective LTV')
plt.legend()
plt.grid(True)
plt.savefig('../output/paper_data/tradfi_ltv.png')
plt.close()

# Chart 7: Reductions Applied and Unique Liquidated Today (TradFi)
plt.figure(figsize=(12, 6))
plt.plot(tradfi_df.index, tradfi_df['reductions_applied_today'], label='Reductions Applied Today')
plt.plot(tradfi_df.index, tradfi_df['unique_liquidated_today'], label='Unique Liquidated Today', linestyle='--')
plt.title('TradFi Reductions and Unique Liquidations Over Time')
plt.xlabel('Date')
plt.ylabel('Count')
plt.legend()
plt.grid(True)
plt.savefig('../output/paper_data/tradfi_reductions_liquidations.png')
plt.close()

print('Charts generated: close_price_comparison.png, price_change_comparison.png, liquidations_comparison.png, health_factor_comparison.png, cumulative_liquidations.png, tradfi_ltv.png, tradfi_reductions_liquidations.png')