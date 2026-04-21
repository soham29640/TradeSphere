import pandas as pd
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands


# Ordered feature list – must stay in sync with LSTM input_size=9
FEATURE_COLS = [
    "Close",
    "SMA_5",
    "SMA_15",
    "RSI",
    "MACD",
    "MACD_Signal",
    "MACD_Diff",
    "BB_High",
    "BB_Low",
]


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute technical indicators and return a clean feature DataFrame.

    Fixes:
    - Squeeze 'Close' to a 1-D Series before passing to `ta` indicators.
      yfinance ≥ 0.2 can return a DataFrame for a single column when columns
      are a MultiIndex, causing ta functions to raise on ndim > 1.
    - Drop rows with NaN *before* selecting final columns so the returned
      DataFrame is always fully populated.
    - Return only the fixed FEATURE_COLS list so the column order that the
      LSTM scaler was fitted on is always honoured.
    """
    df = df.copy()

    # Ensure Close is a plain 1-D Series
    close: pd.Series = df["Close"].squeeze()
    if not isinstance(close, pd.Series):
        raise ValueError("'Close' column could not be reduced to a 1-D Series.")

    df["SMA_5"]      = SMAIndicator(close, window=5).sma_indicator()
    df["SMA_15"]     = SMAIndicator(close, window=15).sma_indicator()
    df["RSI"]        = RSIIndicator(close, window=14).rsi()

    macd             = MACD(close)
    df["MACD"]       = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()
    df["MACD_Diff"]  = macd.macd_diff()

    bb               = BollingerBands(close)
    df["BB_High"]    = bb.bollinger_hband()
    df["BB_Low"]     = bb.bollinger_lband()

    # Drop NaNs first, then select + reorder
    df.dropna(inplace=True)

    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"❌ Indicator columns missing after computation: {missing}")

    return df[FEATURE_COLS]