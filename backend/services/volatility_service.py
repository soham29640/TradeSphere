import pandas as pd
import numpy as np
from arch import arch_model

def get_volatility():
    data = pd.read_csv("data/raw/AAPL.csv")

    data['log_return'] = np.log(data['Close'] / data['Close'].shift(1))
    data.dropna(inplace=True)

    garch_model = arch_model(data['log_return'], vol='GARCH', p=1, q=1)
    garch_fit = garch_model.fit(disp='off')

    forecast = garch_fit.forecast(horizon=1)
    vol = np.sqrt(forecast.variance.values[-1][0])

    return {
        "volatility": float(vol)
    }