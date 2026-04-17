import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, Dense
from tensorflow.keras.activations import softmax
import os
import sys
import random
import matplotlib.pyplot as plt

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from layers.custom_attention import AttentionSum

SEED = 42
os.environ['PYTHONHASHSEED'] = str(SEED)
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

data = pd.read_csv("data/processed/AAPL_cleaned.csv", index_col=0, parse_dates=True)
data['log_return'] = np.log(data['Close'] / data['Close'].shift(1))
data.dropna(subset=['log_return'], inplace=True)

log_return = data['log_return'].values.reshape(-1, 1)
log_return_squared = log_return ** 2

scaler_X = StandardScaler()
log_return_scaled = scaler_X.fit_transform(log_return)

scaler_y = StandardScaler()
log_return_squared_scaled = scaler_y.fit_transform(log_return_squared)

seq_len = 10
x = []
y = []

for i in range(len(log_return_scaled) - seq_len):
    x.append(log_return_scaled[i:i + seq_len])
    y.append(log_return_squared_scaled[i + seq_len])

x = np.array(x)
y = np.array(y)

split = int(len(x) * 0.8)
X_train, X_test = x[:split], x[split:]
y_train, y_test = y[:split], y[split:]

input_layer = Input(shape=(seq_len, 1))
lstm_out = LSTM(32, return_sequences=True)(input_layer)
score = Dense(1)(lstm_out)
attention_weights = softmax(score, axis=1)
context_vector = AttentionSum()([attention_weights, lstm_out])
output = Dense(1, activation='relu')(context_vector)

model = Model(inputs=input_layer, outputs=output)
model.compile(optimizer='adam', loss='mse')
model.fit(X_train, y_train, epochs=30, batch_size=32, verbose=1)

preds = model.predict(X_test)

preds_rescaled = scaler_y.inverse_transform(preds.reshape(-1, 1))
preds_rescaled = np.clip(preds_rescaled, a_min=0, a_max=None)
preds_unscaled = np.sqrt(preds_rescaled).flatten()

true_rescaled = scaler_y.inverse_transform(y_test.reshape(-1, 1))
true_rescaled = np.clip(true_rescaled, a_min=0, a_max=None)
true_unscaled = np.sqrt(true_rescaled).flatten()

plt.figure(figsize=(10, 5))
plt.plot(true_unscaled, label="True Volatility")
plt.plot(preds_unscaled, label="Predicted Volatility")
plt.legend()
plt.title("Attention Volatility Prediction")
plt.savefig("outputs/plots/attention_volatility_plot.png")

model.save("models/attention_model.h5")

prediction_dir = "outputs/predictions"
os.makedirs(prediction_dir, exist_ok=True)
dates = data.index[-len(preds_unscaled):]
pred_df = pd.DataFrame({
    "date": dates,
    "true_volatility": true_unscaled,
    "predicted_volatility": preds_unscaled
})
pred_df.to_csv(os.path.join(prediction_dir, "attention_predictions.csv"), index=False)