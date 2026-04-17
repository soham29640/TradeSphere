from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout,BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.regularizers import l2
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import joblib
import os

from src.utils.data_loader import fetch_data

WINDOW = 60

def prepare_data(series):
    X, y = [], []
    for i in range(len(series) - WINDOW):
        X.append(series[i:i + WINDOW])
        y.append(series[i + WINDOW])
    return np.array(X), np.array(y)

print("📡 Fetching data...")
df = fetch_data("AAPL", interval="5m", period="1mo")  # 🔥 MORE DATA

if df is None or df.empty:
    raise ValueError("No data")

scaler = MinMaxScaler()
scaled = scaler.fit_transform(df['Close'].values.reshape(-1, 1))

X, y = prepare_data(scaled)
X = X.reshape((X.shape[0], X.shape[1], 1))


model = Sequential([

    # 🔹 First LSTM block
    LSTM(128, return_sequences=True, input_shape=(WINDOW, 1)),
    BatchNormalization(),
    Dropout(0.3),

    # 🔹 Second LSTM block
    LSTM(64, return_sequences=True),
    BatchNormalization(),
    Dropout(0.3),

    # 🔹 Third LSTM (captures deeper temporal patterns)
    LSTM(32),
    Dropout(0.2),

    # 🔹 Dense layers (feature extraction)
    Dense(64, activation='relu', kernel_regularizer=l2(0.001)),
    Dense(32, activation='relu'),

    # 🔹 Output layer
    Dense(1)
])

model.compile(optimizer='adam', loss='mse')

early_stop = EarlyStopping(patience=3, restore_best_weights=True)

print("🚀 Training...")
model.fit(
    X, y,
    epochs=20,
    batch_size=32,
    validation_split=0.1,
    callbacks=[early_stop]
)

os.makedirs("models", exist_ok=True)
model.save("models/price_model.h5")
joblib.dump(scaler, "models/scaler.pkl")

print("✅ Model saved")