"""
backend/agent/train_and_save_LSTM_model.py
───────────────────────────────────────────
Train the LSTM and save weights + scaler to models/agent/.

Run from the project root:
    python backend/agent/train_and_save_LSTM_model.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, _ROOT)

import joblib
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader, TensorDataset

from backend.agent.data_loader import fetch_data
from backend.agent.indicator_engine import add_indicators, FEATURE_COLS
from backend.agent.LSTM_model import LSTMModel

# ── Config ────────────────────────────────────────────────────────────────────
TICKER     = "AAPL"
WINDOW     = 78
BATCH_SIZE = 32
EPOCHS     = 50
LR         = 1e-3
VAL_SPLIT  = 0.1

# Updated save paths
SAVE_DIR    = os.path.join(_ROOT, "models", "agent")
MODEL_PATH  = os.path.join(SAVE_DIR, "LSTM_model.ptl")
SCALER_PATH = os.path.join(SAVE_DIR, "standard_scaler.pkl")

os.makedirs(SAVE_DIR, exist_ok=True)

# ── Data ──────────────────────────────────────────────────────────────────────
print(f"📥  Fetching data for {TICKER} …")
raw  = fetch_data(TICKER)
data = add_indicators(raw)
print(f"📊  Dataset shape: {data.shape}")

scaler = StandardScaler()
scaled = scaler.fit_transform(data.values)
joblib.dump(scaler, SCALER_PATH)
print(f"💾  Scaler saved → {SCALER_PATH}")

target_idx = FEATURE_COLS.index("Close")

X, y = [], []
for i in range(len(scaled) - WINDOW - 1):
    X.append(scaled[i : i + WINDOW])
    y.append(scaled[i + WINDOW, target_idx])

X = torch.tensor(np.array(X), dtype=torch.float32)
y = torch.tensor(np.array(y).reshape(-1, 1), dtype=torch.float32)

val_size  = max(1, int(len(X) * VAL_SPLIT))
X_train, X_val = X[:-val_size], X[-val_size:]
y_train, y_val = y[:-val_size], y[-val_size:]

train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=BATCH_SIZE, shuffle=True)
val_loader   = DataLoader(TensorDataset(X_val,   y_val),   batch_size=BATCH_SIZE)
print(f"🗂️   Train: {len(X_train)} | Val: {len(X_val)}")

# ── Training ──────────────────────────────────────────────────────────────────
def train_model() -> None:
    model     = LSTMModel(input_size=len(FEATURE_COLS))
    criterion = nn.MSELoss()
    optimizer = Adam(model.parameters(), lr=LR)
    scheduler = ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
    best_val  = float("inf")

    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_loss = 0.0
        for Xb, yb in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(Xb), yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item()
        train_loss /= len(train_loader)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for Xb, yb in val_loader:
                val_loss += criterion(model(Xb), yb).item()
        val_loss /= len(val_loader)

        prev_lr = optimizer.param_groups[0]["lr"]
        scheduler.step(val_loss)
        new_lr  = optimizer.param_groups[0]["lr"]
        lr_tag  = f"  ⬇ lr→{new_lr:.2e}" if new_lr != prev_lr else ""

        print(f"Epoch {epoch:>3}/{EPOCHS}  train={train_loss:.6f}  val={val_loss:.6f}{lr_tag}")

        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), MODEL_PATH)
            print(f"  ✅ Best saved (val={best_val:.6f})")

    print(f"\n🏁  Done. Model → {MODEL_PATH}")


if __name__ == "__main__":
    train_model()