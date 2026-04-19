"""
train_and_predict.py
────────────────────
Single module that:
  1. Takes df_train (last-day-minus-25min 5-min + today 5-min) from data_loader
  2. Trains a lightweight LSTM in-process (fast enough for 5-min refresh)
  3. Returns (current_close, predicted_close, signal, change_pct)

No files saved to disk. No scheduler. No selector.
Called by paper_app.py once per 5-min refresh when market is live (Condition 1).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset
from torch.optim import Adam


# ── Model ─────────────────────────────────────────────────────────────────────

class _LSTM(nn.Module):
    def __init__(self, input_size: int = 1, hidden: int = 64, layers: int = 2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden, layers, batch_first=True,
                            dropout=0.2 if layers > 1 else 0.0)
        self.drop = nn.Dropout(0.2)
        self.fc   = nn.Linear(hidden, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(self.drop(out[:, -1, :]))


# ── Config ────────────────────────────────────────────────────────────────────
WINDOW    = 60      # 60 × 5-min bars = 5 hours of context
EPOCHS    = 30      # ~2-4 s on CPU for typical intraday dataset
BATCH     = 32
LR        = 1e-3
PATIENCE  = 6
THRESHOLD = 0.15    # % change to flip from HOLD to BUY / SELL


# ── Public function ───────────────────────────────────────────────────────────

def train_and_predict(df_train: pd.DataFrame, ticker: str = "") -> dict:
    """
    Train a fresh LSTM on df_train and predict the next 5-min close.

    Training data composition (Condition 1):
        last-day 5-min (minus first 25 min)  +  today's accumulated 5-min bars

    Parameters
    ----------
    df_train : DataFrame with at least a 'Close' column and WINDOW+10 rows.
    ticker   : optional string for logging.

    Returns
    -------
    dict with keys:
        current_close   : float
        predicted_close : float
        signal          : str   "BUY ✅" | "SELL ❌" | "HOLD ⏸️"
        change_pct      : float
        rmse            : float  (validation RMSE in price units)
        trained_on      : int    (number of rows used)
        error           : str | None
    """
    # ── Guard ─────────────────────────────────────────────────────────────────
    if df_train is None or df_train.empty:
        return _err("No training data provided.")

    df = df_train[["Close"]].dropna().copy()

    if len(df) < WINDOW + 10:
        return _err(f"Not enough rows ({len(df)}) — need at least {WINDOW + 10}.")

    # ── Scale ─────────────────────────────────────────────────────────────────
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df.values)      # (N, 1)

    # ── Sequences ─────────────────────────────────────────────────────────────
    X, y = [], []
    for i in range(len(scaled) - WINDOW - 1):
        X.append(scaled[i : i + WINDOW])
        y.append(scaled[i + WINDOW])

    X = np.array(X, dtype=np.float32)    # (samples, WINDOW, 1)
    y = np.array(y, dtype=np.float32).reshape(-1, 1)

    # Train / val split (last 15% = validation)
    split   = int(len(X) * 0.85)
    X_tr, X_va = X[:split], X[split:]
    y_tr, y_va = y[:split], y[split:]

    X_tr_t = torch.tensor(X_tr)
    y_tr_t = torch.tensor(y_tr)
    X_va_t = torch.tensor(X_va)
    y_va_t = torch.tensor(y_va)

    loader = DataLoader(TensorDataset(X_tr_t, y_tr_t), batch_size=BATCH, shuffle=True)

    # ── Train ─────────────────────────────────────────────────────────────────
    model     = _LSTM(input_size=1)
    criterion = nn.MSELoss()
    opt       = Adam(model.parameters(), lr=LR)

    best_loss  = float("inf")
    best_state = None
    no_imp     = 0

    model.train()
    for _ in range(EPOCHS):
        for xb, yb in loader:
            opt.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            opt.step()

        model.eval()
        with torch.no_grad():
            val_loss = criterion(model(X_va_t), y_va_t).item()
        model.train()

        if val_loss < best_loss:
            best_loss  = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            no_imp     = 0
        else:
            no_imp += 1
            if no_imp >= PATIENCE:
                break

    if best_state:
        model.load_state_dict(best_state)

    # ── Predict next 5-min candle ─────────────────────────────────────────────
    model.eval()
    last_window = scaled[-WINDOW:].reshape(1, WINDOW, 1)
    with torch.no_grad():
        pred_scaled = model(torch.tensor(last_window, dtype=torch.float32)).item()

    predicted_close = float(scaler.inverse_transform([[pred_scaled]])[0][0])
    current_close   = float(df["Close"].iloc[-1])

    # ── RMSE in price units ───────────────────────────────────────────────────
    with torch.no_grad():
        val_pred_scaled = model(X_va_t).numpy()
    val_pred_price = scaler.inverse_transform(val_pred_scaled).flatten()
    val_true_price = scaler.inverse_transform(y_va).flatten()
    rmse = float(np.sqrt(np.mean((val_pred_price - val_true_price) ** 2)))

    # ── Signal ────────────────────────────────────────────────────────────────
    change_pct = (predicted_close - current_close) / current_close * 100
    if change_pct > THRESHOLD:
        signal = "BUY ✅"
    elif change_pct < -THRESHOLD:
        signal = "SELL ❌"
    else:
        signal = "HOLD ⏸️"

    return dict(
        current_close   = current_close,
        predicted_close = predicted_close,
        signal          = signal,
        change_pct      = round(change_pct, 4),
        rmse            = round(rmse, 4),
        trained_on      = len(df),
        error           = None,
    )


def _err(msg: str) -> dict:
    return dict(
        current_close=None, predicted_close=None,
        signal="⚠️ N/A", change_pct=0.0,
        rmse=None, trained_on=0, error=msg,
    )