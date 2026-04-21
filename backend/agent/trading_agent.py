"""
backend/agent/trading_agent.py
───────────────────────────────
Core decision-making agent.

Path updates for new project structure:
    Model:  models/agent/LSTM_model.ptl       (was models/LSTM_model.ptl)
    Scaler: models/agent/standard_scaler.pkl  (was models/standard_scaler.pkl)

All other logic unchanged from the corrected version.
"""

import os
import numpy as np
import joblib
import torch

from backend.agent.LSTM_model import LSTMModel
from backend.agent.data_loader import fetch_data
from backend.agent.indicator_engine import add_indicators, FEATURE_COLS
from backend.agent.alpaca_connector import AlpacaOrder

# ── Paths: resolve relative to project root, not cwd ─────────────────────────
_HERE       = os.path.dirname(os.path.abspath(__file__))           # backend/agent/
_ROOT       = os.path.abspath(os.path.join(_HERE, "..", ".."))     # project root
MODEL_PATH  = os.path.join(_ROOT, "models", "agent", "LSTM_model.ptl")
SCALER_PATH = os.path.join(_ROOT, "models", "agent", "standard_scaler.pkl")

_CLOSE_IDX = FEATURE_COLS.index("Close")


class TradingAgent:
    """
    Args:
        ticker:           Stock symbol to trade, e.g. 'AAPL'.
        window_size:      Number of bars fed into the LSTM (must match training).
        signal_threshold: Minimum predicted price change (fractional) to trigger
                          a BUY or SELL.  Default 0.01 = 1 %.
        sanity_threshold: If the predicted change exceeds this fraction the
                          prediction is likely an artefact – hold instead.
                          Default 0.05 = 5 %.
    """

    def __init__(
        self,
        ticker: str,
        window_size: int = 78,
        signal_threshold: float = 0.01,
        sanity_threshold: float = 0.05,
    ) -> None:
        self.ticker           = ticker
        self.window_size      = window_size
        self.signal_threshold = signal_threshold
        self.sanity_threshold = sanity_threshold
        self.last_action: str | None = None

        self.model  = self._load_model()
        self.scaler = joblib.load(SCALER_PATH)
        self.n_features: int = self.scaler.n_features_in_

        self.alpaca = AlpacaOrder()

    # ── Model ─────────────────────────────────────────────────────────────────
    @staticmethod
    def _load_model() -> LSTMModel:
        model = LSTMModel(input_size=len(FEATURE_COLS))
        state = torch.load(MODEL_PATH, map_location="cpu")
        model.load_state_dict(state)
        model.eval()
        return model

    # ── Data ──────────────────────────────────────────────────────────────────
    def _get_window(self):
        df = fetch_data(self.ticker)
        df = add_indicators(df)
        if len(df) < self.window_size:
            raise ValueError(
                f"Not enough data: need {self.window_size} bars, got {len(df)}."
            )
        return df.iloc[-self.window_size:]

    # ── Prediction ────────────────────────────────────────────────────────────
    def predict(self) -> tuple[float, float]:
        df      = self._get_window()
        current = float(df["Close"].iloc[-1])

        scaled = self.scaler.transform(df.values)
        x = torch.tensor(
            scaled.reshape(1, self.window_size, self.n_features),
            dtype=torch.float32,
        )
        with torch.no_grad():
            pred_scaled = self.model(x).item()

        inv = np.zeros((1, self.n_features), dtype=np.float32)
        inv[0, _CLOSE_IDX] = pred_scaled
        predicted = float(self.scaler.inverse_transform(inv)[0, _CLOSE_IDX])

        return current, predicted

    # ── Decision ──────────────────────────────────────────────────────────────
    def act(self, qty: int = 50) -> tuple[str, float | None, float | None]:
        current, predicted = self.predict()
        change = (predicted - current) / current

        if abs(change) > self.sanity_threshold:
            return "HOLD", current, predicted

        position = self.alpaca.get_position(self.ticker)
        cash     = self.alpaca.get_cash()
        action   = "HOLD"

        if position == 0:
            if change > self.signal_threshold and cash >= current * qty:
                action = "BUY"
        elif position > 0:
            if change < -self.signal_threshold:
                action = "SELL"

        if action == self.last_action:
            return "HOLD", current, predicted

        if action == "BUY":
            self.alpaca.place_order(self.ticker, qty, "buy")
        elif action == "SELL":
            self.alpaca.place_order(self.ticker, position, "sell")

        self.last_action = action
        return action, current, predicted