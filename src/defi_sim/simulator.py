import os
import random
from typing import Dict

from src.position_loader import create_positions
from run_manager import setup_run_directories, get_timeseries_csv_path

# Simulator-level constant
positions_in_pool = 500

RANDOM_SEED = 42


def prepare_positions(n_positions: int = None):
    """Create positions and return a dict keyed by position ID.

    NOTE: With the daily-cohort change this helper is no longer used by the main
    run (positions are now rebuilt each day inside run_full_simulation). Left in
    place for reference / other callers.
    """
    if n_positions is None:
        n_positions = positions_in_pool
    positions_list = create_positions(n_positions)
    # Convert the list to dict: {position_id: position_obj}
    return {pos.position_id: pos for pos in positions_list}


def load_price_df():
    """Load the price dataframe from data_loader.py (must expose df).
    Raises RuntimeError if data_loader is not available or df is missing.
    """
    try:
        from src import data_loader
        price_df = data_loader.df
        return price_df
    except Exception as e:
        raise RuntimeError(
            "data_loader.py must exist and expose a dataframe `df` with 'date' and 'price' columns") from e

# create a new Aave lender
def prepare_aave_simulator():
    from aave.aave_original import AaveSimulator
    return AaveSimulator()

# The actual simulator loop
def run_full_simulation(sim, price_df, n_positions, output_dir: str = '../../output') -> Dict:

    import os
    import csv

    timeseries = []

    total_liquidations_all = 0
    total_dates = 0
    hf_sum_all = 0.0
    hf_count_all = 0
    positions_ever_liquidated = set()

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    random.seed(RANDOM_SEED)

    # loop over each date in the price dataframe
    for idx, (_, row) in enumerate(price_df.iterrows()):
        date = row['date']
        open_price = float(row['open_price'])
        close_price = float(row['close_price'])

        position_objs = {
            p.position_id: p
            for p in create_positions(n_positions, initial_eth_price=open_price)
        }

        # --- DURING DAY: Run liquidation checks at closing price ---
        total_liquidations_day = 0
        liquidated_today = set()
        hf_sum_day = 0.0
        hf_count_day = 0

        daily_csv_rows = []

        # loop over all positions for the trading day
        for pid, pos in position_objs.items():
            pos_value_open = pos.compute_position_value(open_price)
            loan = sim.borrow(pos_value_open) # look up the loan amount for this position

            # Calculate hold value and impermanent loss
            pos_value_close = pos.compute_position_value(close_price)
            hold_value = pos.compute_hold_value(close_price)
            il = pos.compute_impermanent_loss(close_price)

            # Make a liquidation decision and compute a health factor
            decision = sim.decide_liquidation(pos_value_close, loan)
            hf = decision.get('health_factor', float('inf'))
            should_liquidate = decision.get('should_liquidate', False)
            #  Get penalties, if any
            repay_amount = decision.get('repay_amount', 0.0)
            collateral_to_take = decision.get('collateral_to_take', 0.0)

            if hf != float('inf'):
                hf_sum_day += hf
                hf_count_day += 1
                hf_sum_all += hf
                hf_count_all += 1

            if should_liquidate:
                total_liquidations_day += 1
                total_liquidations_all += 1
                liquidated_today.add(pid)
                # NOTE: position IDs repeat each day now (fresh cohort), so this
                # set counts distinct position-SLOTS (max 500), not distinct
                # positions across the whole run. Interpret accordingly.
                positions_ever_liquidated.add(pid)

            # Build row for daily CSV
            csv_row = {
                'position_id': pid,
                'seed_price': f"{open_price:.4f}",
                'position_value_at_seed': f"{pos_value_open:.2f}",
                'loan_amount': f"{loan:.2f}",
                'close_price': f"{close_price:.4f}",
                'position_value_at_close': f"{pos_value_close:.2f}",
                'hold_value': f"{hold_value:.2f}",
                'impermanent_loss': f"{il:.6f}",
                'impermanent_loss_pct': f"{il * 100:.2f}",
                'health_factor': f"{hf:.6f}" if hf != float('inf') else 'inf',
                'should_liquidate': 'Yes' if should_liquidate else 'No',
                'repay_amount': f"{repay_amount:.2f}",
                'collateral_to_take': f"{collateral_to_take:.2f}",
            }
            daily_csv_rows.append(csv_row)

        # --- EXPORT: Generate daily CSV file ---
        date_str = date.strftime('%Y%m%d')
        csv_filename = os.path.join(output_dir, f"trading_day_{date_str}.csv")

        try:
            with open(csv_filename, 'w', newline='') as csvfile:
                fieldnames = [
                    'position_id', 'seed_price', 'position_value_at_seed', 'loan_amount',
                    'close_price', 'position_value_at_close', 'hold_value',
                    'impermanent_loss', 'impermanent_loss_pct',
                    'health_factor', 'should_liquidate', 'repay_amount', 'collateral_to_take'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(daily_csv_rows)
        except Exception as e:
            print(f"Error writing daily CSV for {date_str}: {e}")

        avg_hf_day = (hf_sum_day / hf_count_day) if hf_count_day > 0 else float('inf')

        timeseries.append({
            'date': date,
            'open_price': open_price,
            'close_price': close_price,
            'total_liquidations': total_liquidations_day,
            'unique_liquidated': len(liquidated_today),
            'avg_health_factor': avg_hf_day,
        })

        total_dates += 1

        # Print progress every 100 days
        if (idx + 1) % 100 == 0:
            print(f"Processed {idx + 1} days...")

    avg_hf_all = (hf_sum_all / hf_count_all) if hf_count_all > 0 else float('inf')

    summary = {
        'total_dates': total_dates,
        # NOTE: positions are rebuilt daily, so this is positions PER DAY.
        'total_positions': n_positions,
        'total_liquidations_all': total_liquidations_all,
        'unique_positions_ever_liquidated': len(positions_ever_liquidated),
        'avg_health_factor_all': avg_hf_all,
        'output_dir': output_dir,
    }

    return {
        'timeseries': timeseries,
        'summary': summary,
    }

# the entry point to the simulator
def run_simulation(n_positions, output_dir: str = '../../output', run_id: str = None):

    # Set up all the directories
    run_id, daily_records_dir, charts_dir, run_base_dir = setup_run_directories(output_dir, run_id)

    # Load historical data
    price_df = load_price_df()

    # Setup Aave Lending Simulator
    lender = prepare_aave_simulator()

    # Run simulation over all dates and all positions
    result = run_full_simulation(lender, price_df, n_positions, output_dir=daily_records_dir)

    # Add run metadata to result
    result['run_id'] = run_id
    result['daily_records_dir'] = daily_records_dir
    result['charts_dir'] = charts_dir
    result['run_base_dir'] = run_base_dir

    return result


def generate_price_liquidation_chart(timeseries, output_file: str = 'price_liquidation_chart.png'):

    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("Warning: matplotlib not installed. Skipping chart generation.")
        print("Install with: pip install matplotlib")
        return

    # Extract data from timeseries
    dates = [row['date'] for row in timeseries]
    prices = [row['close_price'] for row in timeseries]
    liquidations = [row['total_liquidations'] for row in timeseries]

    # Create a figure with two Y axes (dual axis plot)
    fig, ax1 = plt.subplots(figsize=(14, 7))

    # Plot price on left Y axis
    color = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('ETH Price (USDC)', color=color)
    line1 = ax1.plot(dates, prices, color=color, linewidth=2, label='ETH Close Price')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)

    # Plot liquidations on right Y axis
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Number of Liquidations', color=color)
    line2 = ax2.plot(dates, liquidations, color=color, linewidth=2, label='Liquidations', linestyle='--')
    ax2.tick_params(axis='y', labelcolor=color)

    # Format X axis to show dates nicely
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    fig.autofmt_xdate(rotation=45, ha='right')

    # Add title and legend
    fig.suptitle('ETH Price vs. Liquidation Events Over Time', fontsize=16, fontweight='bold')
    lines = line1 + line2
    labels = [str(l.get_label()) for l in lines]
    ax1.legend(lines, labels, loc='upper left')

    # Adjust the layout to prevent label cutoff
    fig.tight_layout()

    # Save and display
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {output_file}")
    plt.close()


def export_timeseries_to_csv(timeseries, output_file: str = 'liquidation_timeseries.csv'):

    try:
        import csv
    except ImportError:
        print("Warning: csv module not available")
        return

    try:
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['date', 'open_price', 'close_price', 'price_change', 'number_of_liquidations',
                          'average_health_factor']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header
            writer.writeheader()

            # Write data rows
            for row in timeseries:
                # Calculate price change percentage
                open_price = row['open_price']
                close_price = row['close_price']
                price_change = ((close_price - open_price) / open_price * 100) if open_price != 0 else 0.0

                writer.writerow({
                    'date': row['date'],
                    'open_price': f"{row['open_price']:.2f}",
                    'close_price': f"{row['close_price']:.2f}",
                    'price_change': f"{price_change:.2f}",
                    'number_of_liquidations': row['total_liquidations'],
                    'average_health_factor': f"{row['avg_health_factor']:.6f}" if row['avg_health_factor'] != float(
                        'inf') else 'inf',
                })

        print(f"CSV file saved to: {output_file}")
    except Exception as e:
        print(f"Error writing CSV file: {e}")


if __name__ == "__main__":
    result = run_simulation(positions_in_pool)

    summary = result['summary']
    timeseries = result['timeseries']
    run_id = result['run_id']
    daily_records_dir = result['daily_records_dir']
    charts_dir = result['charts_dir']
    run_base_dir = result['run_base_dir']

    print(f"\n===== RUN ID: {run_id} =====")
    print("===== SIMULATION SUMMARY =====")
    print(f"Total dates simulated: {summary['total_dates']}")
    print(f"Total positions: {summary['total_positions']}")
    print(f"Total liquidation events (all dates): {summary['total_liquidations_all']}")
    print(f"Unique positions ever liquidated: {summary['unique_positions_ever_liquidated']}")
    print(f"Average health factor (all): {summary['avg_health_factor_all']:.4f}")

    # Generate and save the price-liquidation chart
    timeseries_csv_path = get_timeseries_csv_path(run_base_dir)
    price_liq_chart_path = os.path.join(charts_dir, 'price_liquidation_chart.png')
    generate_price_liquidation_chart(timeseries, output_file=price_liq_chart_path)

    # Export timeseries to CSV
    export_timeseries_to_csv(timeseries, output_file=timeseries_csv_path)

    # Call chart generation
    print(f"\nGenerating analysis charts in {charts_dir}...")
    from src.defi_sim.generate_analysis_charts import main as generate_charts_main

    generate_charts_main(output_dir=daily_records_dir, output_charts_dir=charts_dir)

    print(f"\n===== SIMULATION COMPLETE =====")
    print(f"Run ID: {run_id}")
    print(f"Daily records: {daily_records_dir}")
    print(f"Charts: {charts_dir}")
    print(f"Timeseries CSV: {timeseries_csv_path}")