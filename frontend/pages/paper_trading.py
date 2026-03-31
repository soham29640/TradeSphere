import os
import sys
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pandas as pd

from components.sidebar import global_sidebar
ticker = global_sidebar()

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.models.paper_trade import PaperTrader
from src.models.load_and_predict_model import predict_close_price, get_trade_signal

st.set_page_config(layout="wide")
st_autorefresh(interval=60000, key="auto_refresh")
st.markdown("<h2 style='margin-bottom: 0;'>📈 Smart Paper Trading App</h2>", unsafe_allow_html=True)

def fetch_data(ticker="AAPL", interval="1m", period="1d"):
    df = yf.download(ticker, interval=interval, period=period, progress=False)
    if df.empty:
        df = yf.download(ticker, interval="5m", period="5d", progress=False)
        if df.empty:
            raise ValueError(f"No data fetched for ticker: {ticker} (1m and 5m intervals failed)")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if col[1] == '' else col[0] for col in df.columns]
    df = df.reset_index()
    dt_col = df['Datetime'] if 'Datetime' in df.columns else df.index.to_series()
    df['Date'] = dt_col.dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata') if dt_col.dt.tz is None else dt_col.dt.tz_convert('Asia/Kolkata')
    return df

def plot_candlestick(df):
    fig = go.Figure(data=[
        go.Candlestick(
            x=df['Date'], open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name='Candlestick'
        )
    ])
    fig.update_layout(
        title="Live Candlestick Chart",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        yaxis=dict(side="right"),
        margin=dict(t=40, b=20, l=20, r=20),
        height=500
    )
    return fig

if "trader" not in st.session_state:
    st.session_state.trader = PaperTrader(starting_cash=100000)
trader = st.session_state.trader

try:
    df = fetch_data("AAPL")

    if df.empty or df.shape[0] < 5:
        st.error("⚠️ Not enough data to display chart.")
    else:
        current_price = df['Close'].iloc[-1]
        portfolio = trader.status(current_price)

        st.markdown(f"""
            <style>
                #portfolio-box {{
                    position: fixed;
                    top: 3rem;
                    right: 9rem;
                    width: 190px;
                    padding: 12px;
                    background: rgba(40, 40, 40, 0.95);
                    color: white;
                    border-radius: 12px;
                    font-size: 13px;
                    z-index: 9999;
                    box-shadow: 0 0 10px rgba(0,0,0,0.2);
                }}
                #portfolio-box h4 {{
                    font-size: 14px;
                    margin: 0 0 10px 0;
                    text-align: center;
                }}
                #portfolio-box div {{
                    margin-bottom: 6px;
                }}
            </style>

            <div id="portfolio-box">
                <h4>💼 Portfolio</h4>
                <div>💰 <strong>Cash:</strong> ${portfolio['Cash']:.2f}</div>
                <div>📦 <strong>Holdings:</strong> {portfolio['Holdings']}</div>
                <div>💵 <strong>Price:</strong> ${current_price:.2f}</div>
                <div>📈 <strong>Value:</strong> ${float(portfolio['Portfolio Value']):.2f}</div>
            </div>
        """, unsafe_allow_html=True)

        st.plotly_chart(plot_candlestick(df), use_container_width=True)

        st.markdown("---")
        st.subheader("📊 Live Trading Panel")

        quantity = st.number_input("Enter Quantity", min_value=1, value=1)
        minute = datetime.now().minute
        can_trade = (minute % 5 == 0)

        col1, col2 = st.columns(2)
        if can_trade:
            st.success("🟢 Trade window is open (every 5 mins)")
            with col1:
                if st.button("✅ Buy"):
                    msg = trader.buy(current_price, quantity, str(datetime.now()))
                    st.success(msg)
            with col2:
                if st.button("❌ Sell"):
                    msg = trader.sell(current_price, quantity, str(datetime.now()))
                    st.warning(msg)
        else:
            st.info("⏳ You can trade only every 5 minutes.")

        st.markdown("---")
        st.subheader("📒 Trade History")
        st.dataframe(trader.get_trade_dataframe(), use_container_width=True)
        st.markdown("### 🤖 LSTM-Based Price Prediction")

        current, predicted = predict_close_price("AAPL")
        action, change = get_trade_signal(current, predicted)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💵 Current Price", f"${current:.2f}")
        col2.metric("🔮 Predicted Price (Next Close)", f"${predicted:.2f}")
        col3.metric("📊 Estimated Change", f"{change:.2f}%")
        col4.metric("💡 Suggested Action", action)

        with st.expander("📘 About this Prediction", expanded=False):
            st.markdown("""
            - This LSTM (Long Short-Term Memory) model uses the past **78 five-minute candle closes** (approx. 6.5 hours of trading) to predict the **next close price**.
            - It was trained on historical stock data from **1st to 30th day of last month**, using multiple training sessions.
            - The best-performing model (lowest validation loss) was selected.
            - This prediction is **short-term** and does **not consider fundamental news, earnings, or macroeconomic factors**.
            """)

        st.warning("⚠️ This model is a technical predictor only. Do not treat it as financial advice. Always validate with your own research or consult a financial advisor.")

except Exception as e:
    st.error(f"🚫 Error loading data or chart: {e}")
