"""
data_loader.py
──────────────
Pure library — no CLI, no CSV, no scheduler.
Called by paper_app.py on every 5-minute auto-refresh.

Condition 1 (LIVE):
    Market open AND at least 1 bar of today's 5-min data exists.

    Let x = number of today's 5-min bars accumulated so far (dynamic, grows each refresh).

    df_chart  → last-day full 5-min  +  today 1-min  [visual continuity]
    df_train  → today's x bars  +  last-day's LAST (N - x) bars
                i.e. today(x) + lastday(N - x)
                so both halves always mirror each other symmetrically.

    Example:
        today has 5 bars  (25 min) → train on today[5]  + lastday[N-5]
        today has 9 bars  (45 min) → train on today[9]  + lastday[N-9]
        today has 7 bars  (35 min) → train on today[7]  + lastday[N-7]

Condition 2 (CLOSED):
    Market closed OR no today bars yet.
    df_chart  → last complete trading day, 5-min bars (static display only)
    df_train  → empty DataFrame  (no LSTM, no prediction, no trading)
"""

from __future__ import annotations

import pytz
import pandas as pd
import yfinance as yf
from datetime import datetime, time

# ── Timezone / market constants ───────────────────────────────────────────────
ET           = pytz.timezone("America/New_York")
IST          = pytz.timezone("Asia/Kolkata")
MARKET_OPEN  = time(9, 30)
MARKET_CLOSE = time(16, 0)


def is_market_open() -> bool:
    """True while NYSE is open (ignores holidays)."""
    now_et = datetime.now(ET)
    if now_et.weekday() >= 5:
        return False
    t = now_et.time()
    return MARKET_OPEN <= t < MARKET_CLOSE


# ── Internal helpers ──────────────────────────────────────────────────────────

def _flatten(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    return df


def _to_ist(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise index to IST-aware DatetimeIndex, keep only OHLCV."""
    df = _flatten(df).copy()
    df.reset_index(inplace=True)

    for cname in ("Datetime", "Date", "index"):
        if cname in df.columns:
            dt = pd.to_datetime(df[cname])
            break
    else:
        dt = pd.to_datetime(df.iloc[:, 0])

    if dt.dt.tz is None:
        dt = dt.dt.tz_localize("UTC").dt.tz_convert(IST)
    else:
        dt = dt.dt.tz_convert(IST)

    df["Datetime"] = dt
    df = df.set_index("Datetime")

    for col in ("Date", "index", "level_0"):
        if col in df.columns:
            df.drop(columns=col, inplace=True)

    keep = [c for c in ("Open", "High", "Low", "Close", "Volume") if c in df.columns]
    return df[keep].sort_index()


def _dl(ticker: str, **kw) -> pd.DataFrame:
    """Download from yfinance and convert to IST. Returns empty DataFrame on any failure."""
    try:
        raw = yf.download(ticker, progress=False, auto_adjust=True, **kw)
        if raw is None or raw.empty:
            return pd.DataFrame()
        return _to_ist(raw)
    except Exception:
        return pd.DataFrame()


def _has_datetime_index(df: pd.DataFrame) -> bool:
    """True if df has a proper tz-aware DatetimeIndex (not RangeIndex / empty)."""
    return (
        not df.empty
        and isinstance(df.index, pd.DatetimeIndex)
        and df.index.tz is not None
    )


def _bars_for_date(df: pd.DataFrame, target_date) -> pd.DataFrame:
    """Return rows whose index.date == target_date. Safe against non-DatetimeIndex."""
    if not _has_datetime_index(df) or target_date is None:
        return pd.DataFrame()
    return df[df.index.date == target_date]


def _last_two_trading_dates(df: pd.DataFrame):
    """
    Return (prev_date, last_date) from a multi-day DataFrame.
    Returns (None, None) if df is empty or has no DatetimeIndex.
    """
    if not _has_datetime_index(df):
        return None, None
    dates = sorted(set(df.index.date))
    last  = dates[-1] if len(dates) >= 1 else None
    prev  = dates[-2] if len(dates) >= 2 else None
    return prev, last


# ── Public API ────────────────────────────────────────────────────────────────

def get_market_state(ticker: str) -> dict:
    """
    Fetch data and return a state dict consumed by paper_app.py.

    Keys
    ----
    is_live       : bool
    df_chart      : DataFrame for the candlestick chart  (may be empty — caller must guard)
    df_train      : DataFrame for LSTM training          (empty when closed)
    current_price : float
    today_bars    : int     (5-min bars fetched for today)
    last_day_bars : int     (5-min bars from prev session used in training)
    last_updated  : str     (IST clock string)
    fetch_error   : str | None  (set when data could not be fetched)
    """
    open_now = is_market_open()
    now_ist  = pd.Timestamp.now(tz=IST)
    today    = now_ist.date()
    ts       = now_ist.strftime("%H:%M:%S IST")

    # ── Helper: build a CLOSED response ──────────────────────────────────────
    def _closed(df_chart, error=None):
        cp = float(df_chart["Close"].iloc[-1]) if _has_datetime_index(df_chart) else 0.0
        return dict(
            is_live       = False,
            df_chart      = df_chart,
            df_train      = pd.DataFrame(),
            current_price = cp,
            today_bars    = 0,
            last_day_bars = 0,
            last_updated  = ts,
            fetch_error   = error,
        )

    # ── Fetch primary 5-min data ──────────────────────────────────────────────
    df_5m = _dl(ticker, interval="5m", period="5d")

    if not _has_datetime_index(df_5m):
        # Network failure or bad ticker — fall back to daily bars for chart only
        df_daily = _dl(ticker, interval="1d", period="30d")
        return _closed(
            df_daily,
            error=f"Could not fetch 5-min data for '{ticker}'. Check ticker or network."
        )

    prev_date, last_date = _last_two_trading_dates(df_5m)
    df_today_5m   = _bars_for_date(df_5m, today)
    today_bars    = len(df_today_5m)
    df_lastday_5m = _bars_for_date(df_5m, prev_date)   # empty if prev_date is None

    # ── CONDITION 1: LIVE ─────────────────────────────────────────────────────
    if open_now and today_bars >= 1:

        # Chart: full last-day 5-min  +  today 1-min (live ticks for visual)
        df_1m = _dl(ticker, interval="1m", period="1d")
        if _has_datetime_index(df_1m):
            df_chart = pd.concat([df_lastday_5m, df_1m]).sort_index()
        else:
            df_chart = pd.concat([df_lastday_5m, df_today_5m]).sort_index()
        df_chart = df_chart[~df_chart.index.duplicated(keep="last")]

        # ── Dynamic training window (no hardcoding) ───────────────────────────
        # x = today's bar count right now (1 bar on open, grows every 5-min)
        # train = today[x] + lastday[last (N-x) bars]
        # → both halves mirror each other; total ≈ N rows regardless of time of day
        x  = today_bars
        n  = len(df_lastday_5m)
        df_lastday_train = df_lastday_5m.iloc[max(0, n - x):]  # tail of last day

        df_train = pd.concat([df_lastday_train, df_today_5m]).sort_index()
        df_train = df_train[~df_train.index.duplicated(keep="last")]

        current_price = float(df_chart["Close"].iloc[-1])

        return dict(
            is_live       = True,
            df_chart      = df_chart,
            df_train      = df_train,
            current_price = current_price,
            today_bars    = today_bars,
            last_day_bars = len(df_lastday_train),
            last_updated  = ts,
            fetch_error   = None,
        )

    # ── CONDITION 2: CLOSED ───────────────────────────────────────────────────
    # Pick best available chart — prefer most recent complete session.
    if today_bars > 0 and not open_now:
        # Market just closed — today's full session is the best chart
        df_chart = df_today_5m
    elif _has_datetime_index(df_lastday_5m):
        df_chart = df_lastday_5m
    elif last_date is not None:
        df_chart = _bars_for_date(df_5m, last_date)
    else:
        # Last-resort fallback — daily bars
        df_chart = _dl(ticker, interval="1d", period="30d")

    return _closed(df_chart)