import yfinance as yf
import pandas as pd


def fetch_data(ticker: str, interval: str = "5m", period: str = "7d") -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance.

    Fixes:
    - Flatten MultiIndex columns produced by yfinance ≥ 0.2.x when a single
      ticker is requested (yf returns ('Close', 'AAPL') style columns).
    - Always reset the DatetimeIndex so downstream code gets a plain 'Datetime'
      column instead of an index, which prevents KeyError on 'Close'.
    - Raise early with a clear message when the DataFrame is empty.
    """
    df = yf.download(
        ticker,
        interval=interval,
        period=period,
        progress=False,
        auto_adjust=True,
        # Keep a single ticker response flat (no MultiIndex)
        group_by="column",
    )

    if df is None or df.empty:
        raise ValueError(f"❌ No data fetched for ticker '{ticker}'")

    df = df.copy()

    # --- Flatten MultiIndex columns (yfinance ≥ 0.2 quirk) ---------------
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    # --- Ensure a plain integer index with 'Datetime' as a column ---------
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
        # yfinance uses 'Datetime' for intraday and 'Date' for daily
        if "Datetime" not in df.columns and "Date" in df.columns:
            df = df.rename(columns={"Date": "Datetime"})

    # --- Sanity-check required columns ------------------------------------
    required = {"Open", "High", "Low", "Close", "Volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"❌ Fetched data is missing columns: {missing}")

    return df