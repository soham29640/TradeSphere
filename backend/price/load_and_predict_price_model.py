import os
import numpy as np
import joblib
from tensorflow.keras.models import load_model

MODEL_PATH  = "models/price/price_model.h5"
SCALER_PATH = "models/price/scaler.pkl"


def predict_next_prices(df, window_size: int = 60, horizon: int = 10) -> np.ndarray:
    """
    Load the trained LSTM and predict the next `horizon` closing prices.

    Args:
        df          : DataFrame with a 'Close' column (from Yahoo Finance).
        window_size : Number of past bars the model expects (must match training).
        horizon     : How many future bars to predict.

    Returns:
        1-D numpy array of predicted prices in original dollar scale.
    """
    # ── Guards ─────────────────────────────────────────────────────────────────
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at '{MODEL_PATH}'. "
            "Run train_price_model.py first."
        )
    if not os.path.exists(SCALER_PATH):
        raise FileNotFoundError(
            f"Scaler not found at '{SCALER_PATH}'. "
            "Run train_price_model.py first."
        )
    if df is None or df.empty:
        raise ValueError("Input DataFrame is empty.")
    if "Close" not in df.columns:
        raise ValueError("DataFrame must have a 'Close' column.")
    if len(df) < window_size:
        raise ValueError(
            f"Need at least {window_size} rows for prediction; got {len(df)}."
        )

    # ── Load model and scaler ──────────────────────────────────────────────────
    scaler = joblib.load(SCALER_PATH)
    model  = load_model(MODEL_PATH, compile=False)

    # ── Prepare the seed window ────────────────────────────────────────────────
    # Scale the last `window_size` closing prices the same way training did
    scaled = scaler.transform(df["Close"].values.reshape(-1, 1))
    window = scaled[-window_size:].reshape(1, window_size, 1)

    # ── Autoregressive prediction loop ─────────────────────────────────────────
    # Each predicted value is fed back in as the next input bar
    raw_preds = []
    for _ in range(horizon):
        next_val = model.predict(window, verbose=0)[0, 0]
        raw_preds.append(next_val)
        # Drop the oldest bar, append the new prediction at the end
        window = np.concatenate([window[:, 1:, :], [[[next_val]]]], axis=1)

    # ── Convert scaled predictions back to dollar prices ──────────────────────
    prices = scaler.inverse_transform(
        np.array(raw_preds).reshape(-1, 1)
    ).flatten()

    return prices