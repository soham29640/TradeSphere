import os
from data_loader import fetch_data

TICKER = "AAPL"

print("📡 Fetching latest 5-day data...")

df = fetch_data(TICKER, interval="5m", period="5d")

os.makedirs("data", exist_ok=True)
df.to_csv(f"data/raw/price/{TICKER}.csv", index=False)

print("✅ CSV updated")