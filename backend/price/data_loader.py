import time
import pandas as pd
import yfinance as yf

MAX_RETRIES = 2
RETRY_DELAY = 60  # seconds


def fetch_data(ticker: str, interval: str = "5m", period: str = "5d") -> pd.DataFrame:
    """
    Robust OHLCV fetcher using yfinance.

    Handles:
    - Rate limits
    - MultiIndex columns
    - Missing 'Close' (uses 'Adj Close')
    - Dirty/variant schemas

    Returns:
        Clean DataFrame with columns:
        Date, Open, High, Low, Close, Volume
    """

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"📡 Fetching '{ticker}' from Yahoo Finance (attempt {attempt}/{MAX_RETRIES})...")

            df = yf.download(
                ticker,
                interval=interval,
                period=period,
                progress=False,
                threads=False,
                auto_adjust=True
            )

            # 🔴 Empty response (rate limit or API issue)
            if df is None or df.empty:
                raise ValueError("Empty dataframe returned")

            # ✅ Reset index
            df = df.reset_index()

            # ✅ Handle MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # ✅ Clean column names
            df.columns = [col.strip() for col in df.columns]

            # 🔁 Handle Datetime → Date
            if "Datetime" in df.columns:
                df.rename(columns={"Datetime": "Date"}, inplace=True)

            # 🔁 Handle missing Close
            if "Close" not in df.columns:
                if "Adj Close" in df.columns:
                    print("⚠️ 'Close' missing → using 'Adj Close'")
                    df.rename(columns={"Adj Close": "Close"}, inplace=True)
                else:
                    raise ValueError(
                        f"'Close' column missing. Got: {df.columns.tolist()}"
                    )

            # ✅ Validate required columns
            required_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
            missing = [c for c in required_cols if c not in df.columns]

            if missing:
                raise ValueError(
                    f"Missing columns: {missing}. Got: {df.columns.tolist()}"
                )

            # ✅ Select only needed columns
            df = df[required_cols].copy()

            # ✅ Drop invalid rows
            df.dropna(subset=["Close"], inplace=True)
            df.reset_index(drop=True, inplace=True)

            print(f"✅ Fetched {len(df)} rows for '{ticker}'")
            return df

        except Exception as e:
            error_msg = str(e).lower()

            is_rate_limit = any(phrase in error_msg for phrase in (
                "rate limit", "too many requests", "yfratelimiterror", "empty dataframe"
            ))

            if is_rate_limit and attempt < MAX_RETRIES:
                print(f"⚠️ Rate limited. Waiting {RETRY_DELAY}s before retry...")
                time.sleep(RETRY_DELAY)
                continue

            elif is_rate_limit and attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Yahoo Finance rate limit hit after {MAX_RETRIES} attempts."
                ) from e

            else:
                print(f"❌ Failed to fetch '{ticker}': {e}")
                raise