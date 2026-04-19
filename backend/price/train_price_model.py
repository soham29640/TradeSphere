import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.regularizers import l2

from data_loader import fetch_data

# ── Config ─────────────────────────────────────────────────────────────────────
TICKER      = "AAPL"
INTERVAL    = "5m"
PERIOD      = "1mo"    # 1 month of 5-min bars ~ 2000 rows
WINDOW      = 60       # past bars fed into the model
EPOCHS      = 20
BATCH_SIZE  = 32
MODEL_PATH = "models/price/price_model.h5"
SCALER_PATH = "models/price/scaler.pkl"
# ──────────────────────────────────────────────────────────────────────────────


def build_sequences(scaled: np.ndarray, window: int):
    """
    Slide a window over scaled Close prices to build (X, y) pairs.

    X shape : (n_samples, window, 1)
    y shape : (n_samples,)
    """
    X, y = [], []
    for i in range(len(scaled) - window):
        X.append(scaled[i : i + window])
        y.append(scaled[i + window])
    X = np.array(X).reshape(-1, window, 1)
    y = np.array(y)
    return X, y


def build_model(window: int) -> Sequential:
    """3-layer LSTM with BatchNorm and Dropout."""
    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(window, 1)),
        BatchNormalization(),
        Dropout(0.3),

        LSTM(64, return_sequences=True),
        BatchNormalization(),
        Dropout(0.3),

        LSTM(32),
        Dropout(0.2),

        Dense(64, activation="relu", kernel_regularizer=l2(0.001)),
        Dense(32, activation="relu"),
        Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse")
    return model


def train():
    # 1. Fetch real data from Yahoo Finance
    print(f"📡 Fetching data for {TICKER} from Yahoo Finance...")
    df = fetch_data(TICKER, interval=INTERVAL, period=PERIOD)

    if len(df) <= WINDOW:
        raise ValueError(
            f"Not enough data: got {len(df)} rows but need > {WINDOW}. "
            "Try a longer period e.g. period='3mo'."
        )

    print(f"📊 {len(df)} rows available. Building sequences...")

    # 2. Scale Close prices to [0, 1]
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df["Close"].values.reshape(-1, 1))

    # 3. Build sliding-window sequences
    X, y = build_sequences(scaled, WINDOW)
    print(f"   → {len(X)} training sequences created.")

    # 4. Build model
    model = build_model(WINDOW)
    model.summary()

    # 5. Train
    os.makedirs("models", exist_ok=True)

    callbacks = [
        EarlyStopping(patience=3, restore_best_weights=True, verbose=1),
        ModelCheckpoint(MODEL_PATH, save_best_only=True, verbose=1),
    ]

    print("🚀 Training...")
    model.fit(
        X, y,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_split=0.1,
        callbacks=callbacks,
        verbose=1,
    )

    # 6. Save scaler (must match the one used at inference time)
    joblib.dump(scaler, SCALER_PATH)
    print(f"✅ Model  → '{MODEL_PATH}'")
    print(f"✅ Scaler → '{SCALER_PATH}'")


if __name__ == "__main__":
    print("🟢 train() starting...")
    train()