import numpy as np
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from streamlit_autorefresh import st_autorefresh

from src.utils.data_loader import fetch_data
from src.utils.load_and_predict_price_model import predict_next_prices

# ---------------- CONFIG ----------------
st.set_page_config(page_title="VolatiX Dashboard", layout="wide")
st.title("📊 VolatiX: Real-Time Price Prediction")

# 🔥 reduce API pressure
st_autorefresh(interval=180000, key="auto_refresh")  # 3 min

ticker = st.sidebar.text_input("Enter Stock Ticker", value="AAPL")
window_size = 60
horizon = st.sidebar.slider("Prediction Horizon (steps)", 5, 30, 10)

# ---------------- CACHE ----------------
@st.cache_data(ttl=180)
def load_data(ticker):
    return fetch_data(ticker, interval="5m", period="5d")


# ---------------- MAIN ----------------
try:
    with st.spinner("Fetching market data..."):
        df = load_data(ticker)

    # 🔥 safety checks
    if df is None or df.empty:
        st.error("No data available.")
        st.stop()

    required_cols = ["Date", "Open", "High", "Low", "Close"]
    if not all(col in df.columns for col in required_cols):
        st.error("Invalid data format from API.")
        st.stop()

    if len(df) < window_size:
        st.error("Not enough data for prediction.")
        st.stop()

    # ---------------- CANDLE CHART ----------------
    fig = go.Figure(data=[
        go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Market Data'
        )
    ])

    fig.update_layout(
        title=f"📊 {ticker} Price Chart",
        xaxis_rangeslider_visible=False
    )

    # ---------------- PREDICTION ----------------
    with st.spinner("Running AI model..."):
        predictions = predict_next_prices(
            df,
            window_size=window_size,
            horizon=horizon
        )

    # 🔥 time alignment (5 min interval)
    future_time = pd.date_range(
        start=df['Date'].iloc[-1] + pd.Timedelta(minutes=5),
        periods=horizon,
        freq='5min'
    )

    forecast = pd.Series(predictions, index=future_time)

    # ---------------- COMBINED CHART ----------------
    price_fig = go.Figure()

    # last 100 real points
    price_fig.add_trace(go.Scatter(
        x=df['Date'].tail(100),
        y=df['Close'].tail(100),
        mode='lines',
        name='Actual Price'
    ))

    # predicted
    price_fig.add_trace(go.Scatter(
        x=forecast.index,
        y=forecast.values,
        mode='lines+markers',
        name='Predicted Price'
    ))

    price_fig.update_layout(
        title=f"📈 Price Forecast ({horizon*5} min ahead)",
        hovermode='x unified'
    )

    # ---------------- METRICS ----------------
    current_price = df['Close'].iloc[-1]
    next_price = forecast.iloc[0]

    change = next_price - current_price
    percent = (change / current_price) * 100

    col1, col2 = st.columns(2)

    col1.metric("Current Price", f"{current_price:.2f}")
    col2.metric(
        "Next Predicted Price",
        f"{next_price:.2f}",
        f"{percent:.2f}%"
    )

    # ---------------- DISPLAY ----------------
    st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(price_fig, use_container_width=True)

# ---------------- ERROR ----------------
except Exception as e:
    st.error(f"❌ Error: {e}")