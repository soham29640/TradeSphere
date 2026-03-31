import streamlit as st

def global_sidebar():
    st.sidebar.title("⚙️ TradeSphere Controls")

    ticker = st.sidebar.text_input("Enter Stock Ticker", value="AAPL")

    # Save globally
    st.session_state["ticker"] = ticker

    return ticker