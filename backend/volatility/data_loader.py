import yfinance as yf
import pandas as pd
import os
import numpy as np

symbol = "AAPL"
raw_dir = "data/raw"
processed_dir = "data/processed"
os.makedirs(raw_dir, exist_ok=True)
os.makedirs(processed_dir, exist_ok=True)

raw_file = os.path.join(raw_dir, f"{symbol}.csv")
processed_file = os.path.join(processed_dir, f"{symbol}_cleaned.csv")

try:
    df = yf.download(symbol, period="180d", interval="1d", progress=False, timeout=10)
    if df.empty:
        raise ValueError("No data received from Yahoo Finance.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if col[1] == '' else col[0] for col in df.columns]
    df.to_csv(raw_file)
    print("Raw data saved.")

except Exception as e:
    print(f"Download failed: {e}")

    if os.path.exists(raw_file):
        df = pd.read_csv(raw_file)
    else:
        print("No cached file available. Exiting.")
        exit(1)

df['log_return'] = np.log(df['Close'] / df['Close'].shift(1))
df = df[['Open', 'High', 'Low', 'Close', 'Volume','log_return']]
df.dropna(inplace=True)
df.to_csv(processed_file)
print("Cleaned data saved.")

prediction_dir = "outputs/predictions"
prediction_file = os.path.join(prediction_dir,"true_values.csv")
data = pd.read_csv(processed_file)
data["true_volatility"] = data["log_return"].rolling(window=20).std()
data.dropna(inplace=True)
data = data[["Date", "true_volatility"]]
data.to_csv(prediction_file, index=False)
print("true volatility data saved.")