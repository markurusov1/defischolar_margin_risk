import pandas as pd
from pathlib import Path

# Load the price data at the module level
data_path = Path(__file__).parent.parent / 'data' / 'eth-usd-max.csv'
df = pd.read_csv(data_path, parse_dates=['date'])
df = df[['date', 'open_price', 'close_price']].sort_values('date').reset_index(drop=True)
