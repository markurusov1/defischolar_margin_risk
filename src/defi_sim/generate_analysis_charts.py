"""
Chart generation script for analyzing daily liquidation data.

This script reads the daily trading CSV files from the output directory
and generates various analysis charts showing liquidation patterns,
impermanent loss distribution, health factor trends, etc.
"""

import os
import csv
import glob
from datetime import datetime
from typing import List, Dict, Tuple
import statistics


def load_daily_files(output_dir: str = '../output') -> Dict[str, List[Dict]]:
    """Load all daily trading CSV files from the output directory.

    Args:
        output_dir: Directory containing the daily CSV files

    Returns:
        Dict mapping date string to list of position records for that day
    """
    daily_data = {}
    csv_files = sorted(glob.glob(os.path.join(output_dir, 'trading_day_*.csv')))

    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        date_str = filename.replace('trading_day_', '').replace('.csv', '')

        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                records = list(reader)
                daily_data[date_str] = records
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")

    return daily_data


def extract_timeseries(daily_data: Dict[str, List[Dict]]) -> Dict[str, List]:
    """Extract timeseries data from daily records.

    Args:
        daily_data: Dict mapping date to daily records

    Returns:
        Dict with timeseries arrays for various metrics
    """
    dates = []
    liquidation_counts = []
    avg_health_factors = []
    avg_impermanent_losses = []
    seed_prices = []
    close_prices = []
    price_changes = []

    for date_str in sorted(daily_data.keys()):
        records = daily_data[date_str]

        # Extract date
        dates.append(datetime.strptime(date_str, '%Y%m%d'))

        # Count liquidations
        liquidations = sum(1 for r in records if r['should_liquidate'].strip() == 'Yes')
        liquidation_counts.append(liquidations)

        # Calculate average health factor
        hf_values = []
        for r in records:
            hf_str = r['health_factor'].strip()
            if hf_str != 'inf':
                try:
                    hf_values.append(float(hf_str))
                except ValueError:
                    pass
        avg_hf = statistics.mean(hf_values) if hf_values else float('inf')
        avg_health_factors.append(avg_hf)

        # Calculate average impermanent loss
        il_values = []
        for r in records:
            try:
                il_pct = float(r['impermanent_loss_pct'].strip())
                il_values.append(il_pct)
            except ValueError:
                pass
        avg_il = statistics.mean(il_values) if il_values else 0.0
        avg_impermanent_losses.append(avg_il)

        # Extract prices
        if records:
            seed_prices.append(float(records[0]['seed_price']))
            close_prices.append(float(records[0]['close_price']))

    # Calculate daily price changes as percentage
    for i in range(1, len(close_prices)):
        price_change = ((close_prices[i] - close_prices[i - 1]) / close_prices[i - 1]) * 100.0
        price_changes.append(price_change)

    # Prepend 0 for the first day where we don't have a price change
    price_changes.insert(0, 0.0)

    return {
        'dates': dates,
        'liquidation_counts': liquidation_counts,
        'avg_health_factors': avg_health_factors,
        'avg_impermanent_losses': avg_impermanent_losses,
        'seed_prices': seed_prices,
        'close_prices': close_prices,
        'price_changes': price_changes,
    }


def generate_liquidation_chart(timeseries: Dict[str, List], output_file: str = 'liquidation_analysis.png'):
    """Generate a chart showing liquidations over time.

    Args:
        timeseries: Timeseries data dict
        output_file: Path to save the chart
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("Warning: matplotlib not installed. Skipping chart generation.")
        return

    dates = timeseries['dates']
    liquidation_counts = timeseries['liquidation_counts']
    close_prices = timeseries['close_prices']

    fig, ax1 = plt.subplots(figsize=(14, 7))

    # Plot price on left Y axis
    color = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('ETH Close Price (USDC)', color=color)
    line1 = ax1.plot(dates, close_prices, color=color, linewidth=2, label='ETH Close Price')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)

    # Plot liquidations on right Y axis
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Number of Liquidations', color=color)
    line2 = ax2.plot(dates, liquidation_counts, color=color, linewidth=2, label='Liquidations', linestyle='--')
    ax2.tick_params(axis='y', labelcolor=color)

    # Format X axis
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    fig.autofmt_xdate(rotation=45, ha='right')

    # Legend and title
    fig.suptitle('Liquidation Events vs. ETH Price Over Time', fontsize=16, fontweight='bold')
    lines = line1 + line2
    labels = [str(l.get_label()) for l in lines]
    ax1.legend(lines, labels, loc='upper left')

    fig.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {output_file}")
    plt.close()


def generate_health_factor_chart(timeseries: Dict[str, List], output_file: str = 'health_factor_analysis.png'):
    """Generate a chart showing health factor trends over time.

    Args:
        timeseries: Timeseries data dict
        output_file: Path to save the chart
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("Warning: matplotlib not installed. Skipping chart generation.")
        return

    dates = timeseries['dates']
    avg_health_factors = timeseries['avg_health_factors']
    close_prices = timeseries['close_prices']

    fig, ax1 = plt.subplots(figsize=(14, 7))

    # Plot price on left Y axis
    color = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('ETH Close Price (USDC)', color=color)
    line1 = ax1.plot(dates, close_prices, color=color, linewidth=2, label='ETH Close Price')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)

    # Plot health factor on right Y axis
    ax2 = ax1.twinx()
    color = 'tab:green'
    ax2.set_ylabel('Average Health Factor', color=color)
    line2 = ax2.plot(dates, avg_health_factors, color=color, linewidth=2, label='Avg Health Factor', linestyle='--')
    ax2.tick_params(axis='y', labelcolor=color)
    # Add horizontal line at HF=1 (liquidation threshold)
    ax2.axhline(y=1.0, color='red', linestyle=':', linewidth=2, label='Liquidation Threshold (HF=1)')

    # Format X axis
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    fig.autofmt_xdate(rotation=45, ha='right')

    # Legend and title
    fig.suptitle('Average Health Factor vs. ETH Price Over Time', fontsize=16, fontweight='bold')
    lines = line1 + line2
    labels = [str(l.get_label()) for l in lines]
    ax1.legend(lines, labels, loc='upper left')

    fig.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {output_file}")
    plt.close()


def generate_impermanent_loss_chart(timeseries: Dict[str, List], output_file: str = 'impermanent_loss_analysis.png'):
    """Generate a chart showing impermanent loss trends over time.

    Args:
        timeseries: Timeseries data dict
        output_file: Path to save the chart
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("Warning: matplotlib not installed. Skipping chart generation.")
        return

    dates = timeseries['dates']
    avg_impermanent_losses = timeseries['avg_impermanent_losses']
    close_prices = timeseries['close_prices']

    fig, ax1 = plt.subplots(figsize=(14, 7))

    # Plot price on left Y axis
    color = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('ETH Close Price (USDC)', color=color)
    line1 = ax1.plot(dates, close_prices, color=color, linewidth=2, label='ETH Close Price')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)

    # Plot impermanent loss on right Y axis
    ax2 = ax1.twinx()
    color = 'tab:orange'
    ax2.set_ylabel('Average Impermanent Loss (%)', color=color)
    line2 = ax2.plot(dates, avg_impermanent_losses, color=color, linewidth=2, label='Avg Impermanent Loss', linestyle='--')
    ax2.tick_params(axis='y', labelcolor=color)
    # Add horizontal line at IL=0
    ax2.axhline(y=0.0, color='gray', linestyle=':', linewidth=2)

    # Format X axis
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    fig.autofmt_xdate(rotation=45, ha='right')

    # Legend and title
    fig.suptitle('Average Impermanent Loss vs. ETH Price Over Time', fontsize=16, fontweight='bold')
    lines = line1 + line2
    labels = [str(l.get_label()) for l in lines]
    ax1.legend(lines, labels, loc='upper left')

    fig.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {output_file}")
    plt.close()


def generate_combined_dashboard(timeseries: Dict[str, List], output_file: str = 'combined_dashboard.png'):
    """Generate a combined dashboard with all key metrics.

    Args:
        timeseries: Timeseries data dict
        output_file: Path to save the chart
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("Warning: matplotlib not installed. Skipping chart generation.")
        return

    dates = timeseries['dates']
    liquidation_counts = timeseries['liquidation_counts']
    avg_health_factors = timeseries['avg_health_factors']
    avg_impermanent_losses = timeseries['avg_impermanent_losses']
    close_prices = timeseries['close_prices']

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # 1. Liquidations and Price
    color = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('ETH Close Price (USDC)', color=color)
    ax1.plot(dates, close_prices, color=color, linewidth=2, label='ETH Close Price')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)
    ax1_2 = ax1.twinx()
    color = 'tab:red'
    ax1_2.set_ylabel('Liquidations', color=color)
    ax1_2.plot(dates, liquidation_counts, color=color, linewidth=2, label='Liquidations', linestyle='--')
    ax1_2.tick_params(axis='y', labelcolor=color)
    ax1.set_title('Liquidations vs. ETH Price')

    # 2. Health Factor and Price
    color = 'tab:blue'
    ax2.set_xlabel('Date')
    ax2.set_ylabel('ETH Close Price (USDC)', color=color)
    ax2.plot(dates, close_prices, color=color, linewidth=2, label='ETH Close Price')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.grid(True, alpha=0.3)
    ax2_2 = ax2.twinx()
    color = 'tab:green'
    ax2_2.set_ylabel('Avg Health Factor', color=color)
    ax2_2.plot(dates, avg_health_factors, color=color, linewidth=2, label='Avg Health Factor', linestyle='--')
    ax2_2.axhline(y=1.0, color='red', linestyle=':', linewidth=1)
    ax2_2.tick_params(axis='y', labelcolor=color)
    ax2.set_title('Health Factor vs. ETH Price')

    # 3. Impermanent Loss and Price
    color = 'tab:blue'
    ax3.set_xlabel('Date')
    ax3.set_ylabel('ETH Close Price (USDC)', color=color)
    ax3.plot(dates, close_prices, color=color, linewidth=2, label='ETH Close Price')
    ax3.tick_params(axis='y', labelcolor=color)
    ax3.grid(True, alpha=0.3)
    ax3_2 = ax3.twinx()
    color = 'tab:orange'
    ax3_2.set_ylabel('Avg Impermanent Loss (%)', color=color)
    ax3_2.plot(dates, avg_impermanent_losses, color=color, linewidth=2, label='Avg IL', linestyle='--')
    ax3_2.axhline(y=0.0, color='gray', linestyle=':', linewidth=1)
    ax3_2.tick_params(axis='y', labelcolor=color)
    ax3.set_title('Impermanent Loss vs. ETH Price')

    # 4. All metrics on one chart (with normalized axes for comparison)
    ax4.plot(dates, liquidation_counts, linewidth=2, label='Liquidations', linestyle='-')
    ax4_2 = ax4.twinx()
    ax4_2.plot(dates, avg_health_factors, linewidth=2, label='Avg HF', linestyle='--', color='green')
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Liquidation Count', color='tab:blue')
    ax4_2.set_ylabel('Avg Health Factor', color='green')
    ax4.grid(True, alpha=0.3)
    ax4.set_title('Liquidations and Health Factor Combined')
    ax4.tick_params(axis='y', labelcolor='tab:blue')
    ax4_2.tick_params(axis='y', labelcolor='green')

    # Format X axes
    for ax in [ax1, ax2, ax3, ax4]:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    fig.suptitle('Liquidation Analysis Dashboard', fontsize=16, fontweight='bold')
    fig.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {output_file}")
    plt.close()


def generate_price_distribution_chart(daily_data: Dict[str, List[Dict]], output_file: str = 'price_distribution.png'):
    """Generate a chart showing distribution of impermanent loss by price levels.

    Args:
        daily_data: Daily data dict from load_daily_files
        output_file: Path to save the chart
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Warning: matplotlib not installed. Skipping chart generation.")
        return

    price_to_il = {}

    for date_str in daily_data.keys():
        records = daily_data[date_str]
        for record in records:
            try:
                close_price = float(record['close_price'])
                il_pct = float(record['impermanent_loss_pct'])

                # Bucket prices into ranges
                price_bucket = int(close_price / 100) * 100  # Bucket by 100 USDC

                if price_bucket not in price_to_il:
                    price_to_il[price_bucket] = []
                price_to_il[price_bucket].append(il_pct)
            except ValueError:
                pass

    # Calculate average IL for each price bucket
    prices = sorted(price_to_il.keys())
    avg_ils = [statistics.mean(price_to_il[p]) if price_to_il[p] else 0 for p in prices]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(range(len(prices)), avg_ils, color='steelblue', alpha=0.7)
    ax.set_xlabel('Price Bucket (USDC)')
    ax.set_ylabel('Average Impermanent Loss (%)')
    ax.set_title('Average Impermanent Loss by Price Level')
    ax.set_xticks(range(len(prices)))
    ax.set_xticklabels([f'${p}' for p in prices], rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')

    fig.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {output_file}")
    plt.close()


def generate_price_change_liquidation_correlation_chart(timeseries: Dict[str, List], output_file: str = 'price_change_liquidation_correlation.png'):
    """Generate a chart showing correlation between price change and liquidations.

    Args:
        timeseries: Timeseries data dict with dates, price_changes, liquidation_counts
        output_file: Path to save the chart
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("Warning: matplotlib not installed. Skipping price change correlation chart.")
        return

    price_changes = timeseries.get('price_changes', [])
    liquidation_counts = timeseries.get('liquidation_counts', [])
    dates = timeseries.get('dates', [])

    if not price_changes or not liquidation_counts:
        print("Warning: No price change or liquidation data available.")
        return

    # Calculate correlation
    try:
        correlation = np.corrcoef(price_changes, liquidation_counts)[0, 1]
    except:
        correlation = 0.0

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # Subplot 1: Scatter plot with trend line
    ax1.scatter(price_changes, liquidation_counts, alpha=0.6, s=30, color='steelblue')

    # Add trend line
    try:
        z = np.polyfit(price_changes, liquidation_counts, 1)
        p = np.poly1d(z)
        x_trend = np.linspace(min(price_changes), max(price_changes), 100)
        ax1.plot(x_trend, p(x_trend), "r-", linewidth=2, label=f'Trend (r={correlation:.4f})')
    except:
        pass

    ax1.set_xlabel('Price Change (%)', fontsize=12)
    ax1.set_ylabel('Number of Liquidations', fontsize=12)
    ax1.set_title('Correlation: Price Change vs Liquidations (Scatter Plot)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Subplot 2: Time series showing both metrics
    ax2_twin = ax2.twinx()

    # Plot price change on left axis
    color = 'tab:blue'
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Price Change (%)', color=color, fontsize=12)
    line1 = ax2.plot(dates, price_changes, color=color, linewidth=1.5, label='Price Change', alpha=0.7)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.grid(True, alpha=0.3)

    # Plot liquidations on right axis
    color = 'tab:red'
    ax2_twin.set_ylabel('Number of Liquidations', color=color, fontsize=12)
    line2 = ax2_twin.plot(dates, liquidation_counts, color=color, linewidth=1.5, label='Liquidations', alpha=0.7)
    ax2_twin.tick_params(axis='y', labelcolor=color)

    ax2.set_title('Price Change vs Liquidations Over Time', fontsize=14, fontweight='bold')

    # Format x-axis
    fig.autofmt_xdate(rotation=45, ha='right')

    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc='upper left')

    # Adjust layout
    fig.tight_layout()

    # Save chart
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {output_file}")
    plt.close()

    # Print correlation info
    print(f"\nPrice Change - Liquidation Correlation Statistics:")
    print(f"  Correlation Coefficient: {correlation:.4f}")
    if abs(correlation) < 0.3:
        strength = "weak"
    elif abs(correlation) < 0.7:
        strength = "moderate"
    else:
        strength = "strong"
    direction = "positive" if correlation > 0 else "negative"
    print(f"  Interpretation: {strength.capitalize()} {direction} correlation")


def main(output_dir: str = 'output', output_charts_dir: str = None):
    """Main entry point for chart generation.

    Args:
        output_dir: Directory containing daily CSV files
        output_charts_dir: Directory to save generated charts (if None, uses current directory)
    """
    if output_charts_dir is None:
        output_charts_dir = ''

    print("Loading daily trading files...")
    daily_data = load_daily_files(output_dir)

    if not daily_data:
        print("No daily files found in", output_dir)
        return

    print(f"Loaded {len(daily_data)} trading days")

    print("\nExtracting timeseries data...")
    timeseries = extract_timeseries(daily_data)

    print("\nGenerating charts...")
    generate_liquidation_chart(timeseries, os.path.join(output_charts_dir, 'liquidation_analysis.png'))
    generate_health_factor_chart(timeseries, os.path.join(output_charts_dir, 'health_factor_analysis.png'))
    generate_impermanent_loss_chart(timeseries, os.path.join(output_charts_dir, 'impermanent_loss_analysis.png'))
    generate_combined_dashboard(timeseries, os.path.join(output_charts_dir, 'combined_dashboard.png'))
    generate_price_distribution_chart(daily_data, os.path.join(output_charts_dir, 'price_distribution.png'))
    generate_price_change_liquidation_correlation_chart(timeseries, os.path.join(output_charts_dir, 'price_change_liquidation_correlation.png'))

    print("\nAll charts generated successfully!")


if __name__ == "__main__":
    main()
