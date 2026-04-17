import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import matplotlib.pyplot as plt
import tensorflow as tf
import os

data = pd.read_csv("data/raw/AAPL.csv", index_col=0, parse_dates=True)
data['Close'] = pd.to_numeric(data['Close'], errors='coerce')
data['log_return'] = np.log(data['Close'] / data['Close'].shift(1))
data.dropna(subset=['log_return'], inplace=True)

log_return = data['log_return'].values.reshape(-1, 1)
log_return_squared = log_return ** 2

scaler_X = StandardScaler()
log_return_scaled = scaler_X.fit_transform(log_return)

scaler_y = StandardScaler()
log_return_squared_scaled = scaler_y.fit_transform(log_return_squared)

seq_len = 10
X, y = [], []
for i in range(len(log_return_scaled) - seq_len):
    X.append(log_return_scaled[i:i+seq_len])
    y.append(log_return_squared_scaled[i + seq_len])

X, y = np.array(X), np.array(y)

split = int(len(X) * 0.8)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

model = Sequential([
    LSTM(64, input_shape=(seq_len, 1), return_sequences=False),
    Dense(1)
])

model.compile(optimizer='adam', loss='mse')
model.fit(X_train, y_train, epochs=30, batch_size=16, validation_split=0.1, verbose=1)

preds = model.predict(X_test)

preds_rescaled = scaler_y.inverse_transform(preds.reshape(-1, 1))
preds_rescaled = np.maximum(preds_rescaled, 0)
preds_unscaled = np.sqrt(preds_rescaled).flatten()

true_rescaled = scaler_y.inverse_transform(y_test.reshape(-1, 1))
true_rescaled = np.maximum(true_rescaled, 0)
true_unscaled = np.sqrt(true_rescaled).flatten()

plt.figure(figsize=(10, 5))
plt.plot(true_unscaled, label="True Volatility")
plt.plot(preds_unscaled, label="Predicted Volatility")
plt.legend()
plt.title("LSTM Volatility Prediction")
os.makedirs("outputs/plots", exist_ok=True)
plt.savefig("outputs/plots/lstm_volatility_plot.png")

os.makedirs("models", exist_ok=True)
model.save("models/lstm_model.h5")

prediction_dir = "outputs/predictions"
os.makedirs(prediction_dir, exist_ok=True)
dates = data.index[-len(preds_unscaled):]
pred_df = pd.DataFrame({
    "date": dates,
    "true_volatility": true_unscaled,
    "predicted_volatility": preds_unscaled
})
pred_df.to_csv(os.path.join(prediction_dir, "lstm_predictions.csv"), index=False)
