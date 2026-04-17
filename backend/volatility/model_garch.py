import pandas as pd
import numpy as np
from arch import arch_model
import os

data = pd.read_csv("data/processed/AAPL_cleaned.csv", index_col=0, parse_dates=True)
log_return = data["log_return"].dropna()

rolling_window = 145
predicted_vols = []
dates = []

for i in range(rolling_window, len(log_return)):
    train_data = log_return[i - rolling_window:i]
    model = arch_model(train_data, vol='GARCH', p=1, q=1)
    model_fit = model.fit(disp='off')
    forecast = model_fit.forecast(horizon=1)
    vol = np.sqrt(forecast.variance.values[-1][0])
    predicted_vols.append(vol)
    dates.append(log_return.index[i])

garch_df = pd.DataFrame({
    "date": dates,
    "predicted_volatility": predicted_vols
})
garch_df.set_index("date", inplace=True)

os.makedirs("outputs/predictions", exist_ok=True)
garch_df.to_csv("outputs/predictions/garch_predictions.csv")
print("Rolling GARCH predictions saved.")

import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(garch_df["predicted_volatility"], label="Rolling GARCH(1,1) Predicted Volatility", color='blue')
plt.title("Rolling GARCH(1,1) Volatility Forecast")
plt.xlabel("Date")
plt.ylabel("Volatility")
plt.legend()
plt.grid(True)
plt.tight_layout()

os.makedirs("outputs/plots", exist_ok=True)
plt.savefig("outputs/plots/garch_rolling_plot.png")
plt.show()
