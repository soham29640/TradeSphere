import yfinance as yf
import requests
import pandas as pd
from dotenv import load_dotenv
import os
from pathlib import Path

# ---------------- ENV ----------------
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

API_KEY = os.getenv("ALPHA_API_KEY")

print("🔑 API KEY LOADED:", API_KEY is not None)


# ---------------- YAHOO ----------------
def fetch_from_yahoo(ticker, interval, period):
    try:
        df = yf.download(
            ticker,
            interval=interval,
            period=period,
            progress=False,
            threads=False
        )

        if df is not None and not df.empty:
            df = df.reset_index()

            # ✅ Normalize column name
            if 'Datetime' in df.columns:
                df.rename(columns={'Datetime': 'Date'}, inplace=True)

            print("✅ Yahoo success")
            return df

    except Exception as e:
        print("❌ Yahoo error:", e)

    return None


# ---------------- ALPHA VANTAGE ----------------
def fetch_from_alpha(ticker):
    if not API_KEY:
        print("❌ Alpha API key missing")
        return None

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",   # 🔥 FREE endpoint
        "symbol": ticker,
        "apikey": API_KEY
    }

    try:
        r = requests.get(url, params=params, timeout=10)

        if r.status_code != 200:
            print("❌ Alpha HTTP error:", r.status_code)
            return None

        data = r.json()
        print("🔍 Alpha response:", data)

        if "Note" in data or "Error Message" in data or "Information" in data:
            print("⚠️ Alpha API issue")
            return None

        key = "Time Series (Daily)"
        if key not in data:
            return None

        df = pd.DataFrame.from_dict(data[key], orient='index')
        df.columns = ["Open", "High", "Low", "Close", "Volume"]

        df = df.astype(float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        df.reset_index(inplace=True)
        df.rename(columns={"index": "Date"}, inplace=True)

        print("✅ Alpha success (daily data)")
        return df

    except Exception as e:
        print("❌ Alpha error:", e)
        return None
    

# ---------------- MAIN FUNCTION ----------------
def fetch_data(ticker, interval="5m", period="5d"):

    # 🔥 1. Try Yahoo
    df = fetch_from_yahoo(ticker, interval, period)
    if df is not None:
        return df

    # 🔥 2. Try Alpha
    print("⚠️ Switching to Alpha Vantage...")
    df = fetch_from_alpha(ticker)
    if df is not None:
        return df

    # 🔥 3. FINAL FALLBACK (never crash)
    print("⚠️ Using fallback sample data...")

    dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='5min')
    prices = pd.Series(range(100)) + 100

    df = pd.DataFrame({
        "Date": dates,
        "Open": prices,
        "High": prices + 1,
        "Low": prices - 1,
        "Close": prices,
        "Volume": 1000
    })

    return df