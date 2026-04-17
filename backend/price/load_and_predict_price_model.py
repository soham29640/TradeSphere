import numpy as np
import joblib
import os
from tensorflow.keras.models import load_model


def predict_next_prices(df, window_size=60, horizon=10):

    # ✅ Model existence check
    if not os.path.exists("models/price_model.h5"):
        raise FileNotFoundError("Model not found. Train first.")

    if not os.path.exists("models/scaler.pkl"):
        raise FileNotFoundError("Scaler not found. Train first.")

    # ✅ Data validation
    if df is None or df.empty:
        raise ValueError("Input dataframe is empty")

    if 'Close' not in df.columns:
        raise ValueError("Missing 'Close' column in dataframe")

    if len(df) < window_size:
        raise ValueError("Not enough data for prediction")

    # 🔄 Load model + scaler
    scaler = joblib.load("models/scaler.pkl")
    model = load_model("models/price_model.h5", compile=False)

    # 🔢 Prepare input
    close_prices = df['Close'].values.reshape(-1, 1)
    scaled = scaler.transform(close_prices)

    inputs = scaled[-window_size:].reshape(1, window_size, 1)

    predictions = []

    # 🔮 Predict future
    for _ in range(horizon):
        next_pred = model.predict(inputs, verbose=0)[0][0]
        predictions.append(next_pred)

        # shift window
        inputs = np.concatenate(
            (inputs[:, 1:, :], [[[next_pred]]]),
            axis=1
        )

    # 🔙 Inverse scaling
    predicted_prices = scaler.inverse_transform(
        np.array(predictions).reshape(-1, 1)
    ).flatten()

    return predicted_prices