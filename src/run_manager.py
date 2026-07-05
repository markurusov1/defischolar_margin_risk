# Simulator utilities
import os
from datetime import datetime


# Generate a unique run ID based on the current timestamp
def generate_run_id():
    return datetime.now().strftime('run_%Y%m%d_%H%M%S')


# Create the directory structure under the output base directory
def setup_run_directories(base_output_dir: str = '../../output', run_id: str = None):
    if run_id is None:
        run_id = generate_run_id()

    run_base_dir = os.path.join(base_output_dir, run_id)
    daily_records_dir = os.path.join(run_base_dir, 'daily_records')
    charts_dir = os.path.join(run_base_dir, 'charts')

    os.makedirs(daily_records_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)

    return run_id, daily_records_dir, charts_dir, run_base_dir


# Get the path for the timeseries CSV file in a given run directory.
def get_timeseries_csv_path(run_base_dir: str):
    return os.path.join(run_base_dir, 'liquidation_timeseries.csv')


# Get the most recent run ID from the output directory.
def get_latest_run_id(base_output_dir: str = 'output'):
    if not os.path.exists(base_output_dir):
        return None

    run_dirs = [d for d in os.listdir(base_output_dir)
                if os.path.isdir(os.path.join(base_output_dir, d))
                and d.startswith('run_')]

    if not run_dirs:
        return None

    return sorted(run_dirs)[-1]


if __name__ == "__main__":
    # Test run ID generation
    run_id = generate_run_id()
    print(f"Generated run ID: {run_id}")

    # Test directory setup
    run_id, daily_dir, charts_dir, base_dir = setup_run_directories()
    print(f"Created directories:")
    print(f"  Run base: {base_dir}")
    print(f"  Daily records: {daily_dir}")
    print(f"  Charts: {charts_dir}")
    print(f"  Timeseries CSV: {get_timeseries_csv_path(base_dir)}")
