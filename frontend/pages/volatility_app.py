import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import matplotlib.pyplot as plt
from arch import arch_model
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Layer
import tensorflow.keras.backend as K

class AttentionSum(Layer):
    def call(self, inputs):
        attention, lstm_output = inputs
        return K.sum(attention * lstm_output, axis=1)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(page_title="📊 Volatility Risk Dashboard", layout="wide")
st.title("📈 Stock Volatility Forecast & Risk Analysis")

st.markdown("""
### 🔎 Overview
This dashboard forecasts and compares the volatility of a given stock using:
- GARCH (Generalized Autoregressive Conditional Heteroskedasticity)
- LSTM (Long Short-Term Memory neural network)
- Attention-based LSTM

Each model predicts next-day volatility. These predictions are compared to the 75th percentile of historical volatility to determine risk.
""")

st.sidebar.header("⚙️ Settings")
num_days = st.sidebar.slider("Select number of past days to use", min_value=150, max_value=250, value=200, step=10)

st.sidebar.header("📤 Upload Returns Data")
file = st.sidebar.file_uploader("Upload returns.csv", type=["csv"])

if file:
    data = pd.read_csv(file, index_col=0, parse_dates=True)
else:
    data = pd.read_csv("data/raw/AAPL.csv", index_col=0, parse_dates=True)

data['Close'] = pd.to_numeric(data['Close'], errors='coerce')
data['log_return'] = np.log(data['Close'] / data['Close'].shift(1))
data = data.tail(num_days)
data.dropna(subset=['log_return'], inplace=True)

st.subheader("📄 Raw Data Preview")
st.dataframe(data.tail(10))

log_return = data['log_return'].values.reshape(-1, 1)
log_return_squared = log_return ** 2

scaler_standard = StandardScaler()
scaled_standard = scaler_standard.fit_transform(log_return)

scaler_squared_standard = StandardScaler()
scaled_squared_standard = scaler_squared_standard.fit_transform(log_return_squared)

seq_len = 10
X_lstm, y_lstm, X_attn, y_attn = [], [], [], []

for i in range(len(scaled_standard) - seq_len):
    X_lstm.append(scaled_standard[i:i+seq_len])
    y_lstm.append(scaled_squared_standard[i + seq_len])

for i in range(len(scaled_standard) - seq_len):
    X_attn.append(scaled_standard[i:i+seq_len])
    y_attn.append(scaled_squared_standard[i + seq_len])

X_lstm, y_lstm = np.array(X_lstm), np.array(y_lstm)
X_attn, y_attn = np.array(X_attn), np.array(y_attn)

LOW_RISK_LABEL = "🟢 Low Risk"
HIGH_RISK_LABEL = "🔴 High Risk"

lstm_model = load_model("models/lstm_model.h5")
X_next_lstm = scaled_standard[-seq_len:].reshape(1, seq_len, 1)
pred_lstm_next = lstm_model.predict(X_next_lstm)
pred_lstm_rescaled = np.clip(scaler_squared_standard.inverse_transform(pred_lstm_next), 0, None)
lstm_next_vol = np.sqrt(pred_lstm_rescaled)[0][0]

attn_model = load_model("models/attention_model.h5", custom_objects={"AttentionSum": AttentionSum})
X_next_attn = scaled_standard[-seq_len:].reshape(1, seq_len, 1)
pred_attn_next = attn_model.predict(X_next_attn)
pred_attn_rescaled = np.clip(scaler_squared_standard.inverse_transform(pred_attn_next), 0, None)
attn_next_vol = np.sqrt(pred_attn_rescaled)[0][0]

garch_model = arch_model(log_return.squeeze(), vol='GARCH', p=1, q=1)
garch_fit = garch_model.fit(disp='off')
garch_forecast = garch_fit.forecast(horizon=1)
garch_next_vol = np.sqrt(garch_forecast.variance.values[-1][0])

rolling_window = min(num_days, len(log_return_squared))
threshold_days = min(rolling_window, len(scaled_squared_standard))
vol_history = np.sqrt(scaler_squared_standard.inverse_transform(scaled_squared_standard[-threshold_days:]))
threshold = np.percentile(vol_history, 75)

lstm_risk = HIGH_RISK_LABEL if lstm_next_vol > threshold else LOW_RISK_LABEL
attn_risk = HIGH_RISK_LABEL if attn_next_vol > threshold else LOW_RISK_LABEL
garch_risk = HIGH_RISK_LABEL if garch_next_vol > threshold else LOW_RISK_LABEL

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(data.index[-100:], data['log_return'].rolling(window=20).std().dropna()[-100:], label="📉 Historical Volatility")
ax.axhline(y=lstm_next_vol, color='blue', linestyle=':', label='🔵 LSTM Forecast')
ax.axhline(y=attn_next_vol, color='orange', linestyle=':', label='🟠 Attention-LSTM Forecast')
ax.axhline(y=garch_next_vol, color='green', linestyle=':', label='🟢 GARCH Forecast')
ax.axhline(y=threshold, color='red', linestyle='--', label='🔺 75% Threshold (Volatility)')
ax.set_title("📈 Volatility Forecast vs Historical")
ax.set_ylabel("Volatility")
ax.set_xlabel("Date")
ax.legend()
fig.tight_layout()
st.pyplot(fig)

st.subheader("📌 Forecast Summary")
st.write(f"🔵 LSTM Next Volatility: **{lstm_next_vol:.6f}** — {lstm_risk}")
st.write(f"🟠 Attention-LSTM Next Volatility: **{attn_next_vol:.6f}** — {attn_risk}")
st.write(f"🟢 GARCH Next Volatility: **{garch_next_vol:.6f}** — {garch_risk}")

st.subheader("📊 Model Evaluation")
st.markdown("""
The chart below compares the performance of each model based on three metrics:

- **MSE (Mean Squared Error)**: Penalizes larger errors more heavily
- **RMSE (Root Mean Squared Error)**: Interpretable in the same units as volatility
- **MAE (Mean Absolute Error)**: Averages the absolute differences between predicted and actual volatility

📌 **How to use this**:
- Lower values generally indicate a better-performing model.
- Use this chart to understand each model’s accuracy before relying solely on its prediction.
- Combine this with the forecast graph above for a balanced decision.

⚠️ Keep in mind that while one model may perform slightly better statistically, it may not always generalize well in live market conditions.
""")
eval_img = Image.open("outputs/plots/evaluation.png")
st.image(eval_img, caption="📉 RMSE, MSE, and MAE Comparison for GARCH, LSTM, and Attention-LSTM", use_column_width=True)
