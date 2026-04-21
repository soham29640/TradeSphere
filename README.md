# 🌐 TradeSphere

<div align="center">

> **A full-stack AI-powered stock market intelligence platform** — combining real-time price prediction, volatility forecasting, chart pattern recognition, live paper trading, and a Gemini-powered AI assistant in one cohesive, production-ready dashboard.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![PyTorch](https://img.shields.io/badge/PyTorch-ResNet--18-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-LSTM-FF6F00?logo=tensorflow&logoColor=white)](https://www.tensorflow.org/)
[![Google Gemini](https://img.shields.io/badge/Gemini-AI%20Assistant-4285F4?logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e)](LICENSE)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Platform Modules](#-platform-modules)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Usage](#-usage)
- [Models](#-models)
- [Configuration](#-configuration)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔭 Overview

TradeSphere is a modular, production-grade machine learning platform for stock market intelligence. It unifies six independent components — each backed by purpose-built ML models and interactive Streamlit dashboards — to deliver a complete, 360° view of the market for traders, quant analysts, and ML practitioners.

| Module | Purpose | Core Technology |
|---|---|---|
| **🏠 Home** | Live ticker tape, sector heat-map, market overview | Streamlit, custom HTML/CSS |
| **📈 Price Prediction** | Forecast next N 5-minute price steps | 3-layer stacked LSTM (TensorFlow/Keras) |
| **📊 Volatility Forecast** | Next-day risk classification | GARCH · LSTM · Attention-LSTM (ensemble) |
| **🔍 Pattern Detection** | Identify 20 chart patterns from images | ResNet-18 CNN (PyTorch, transfer learning) |
| **💹 Paper Trading** | Simulated live trading with AI signals | LSTM retrain every 5 min, rule-based engine |
| **🎯 Daily Quests** | AI-generated daily trading challenges | Google Gemini Pro |
| **🤖 Trading Agent** | Automated Alpaca paper/live trading bot | LSTM + technical indicators, alpaca-py SDK |

---

## ✨ Features

### Core Analytics
- **📈 Real-Time Price Prediction** — Fetches live 5-minute OHLCV data via `yfinance`, normalises it with `MinMaxScaler`, and runs a deep 3-layer LSTM to predict the next 5–30 price steps — rendered as an interactive Plotly candlestick chart with a live forecast overlay.
- **📊 Volatility Risk Dashboard** — Computes next-day volatility with three competing models (GARCH, LSTM, Attention-LSTM) and instantly classifies each forecast as **🟢 Low Risk** or **🔴 High Risk** against the rolling 75th-percentile threshold.
- **🔍 Chart Pattern Recognition** — Upload any candlestick chart image and receive the top-3 pattern predictions with confidence percentages from a fine-tuned ResNet-18 model trained across 20 classical pattern classes.

### Paper Trading Engine
- **💹 Live Paper Trading** — A full simulated trading environment that retrains the LSTM on 5-minute bars every 5 minutes during market hours, opens a **1-minute trade window** after each retrain, and locks trading for the subsequent 4 minutes — mirroring real-world execution constraints.
- **🛑 Stop-Loss & Risk Guardrails** — Automatic stop-loss enforcement (configurable % below average cost), maximum position size cap, and per-trade P&L tracking with a full audit log.
- **📉 Portfolio Metrics** — Real-time unrealised P&L, realised P&L, portfolio value, total return %, and a timestamped trade ledger exportable as a DataFrame.

### Intelligence & Gamification
- **🤖 Trading Agent** — An Alpaca-connected automated trading bot that uses a pretrained LSTM (with RSI, SMA, MACD, and Bollinger Band features) to predict the next price move and submit market orders via the `alpaca-py` SDK. Supports both paper and live trading modes with configurable ticker, quantity, and interval.
- **🎯 Daily Quests** — Gemini-generated daily trading challenges that refresh each day, providing educational market exercises to sharpen analytical skills.
- **🌡 Market Heat-Map** — A real-time sector heat-map across Technology, Financials, Healthcare, Energy, Consumer, and Comm Services with colour-coded % changes.
- **📡 Live Ticker Tape** — A continuously scrolling ticker strip for 15 major symbols (equities, indices, crypto, commodities).

### Platform
- **⚡ Auto-Refresh** — Dashboards auto-refresh on configurable cadences (3 min for price, 5 min for paper trading) using `streamlit-autorefresh`.
- **📤 Custom Data Upload** — The volatility dashboard accepts a user-uploaded `returns.csv` to analyse any asset beyond the built-in defaults.

---

## 🏗 Architecture

```
                              ┌──────────────────────┐
                              │     User / Browser   │
                              └──────────┬───────────┘
                                         │
                              ┌──────────▼───────────┐
                              │   Streamlit Frontend  │
            ┌─────────────────┼───────────────────────┼─────────────────┐
            │                 │                       │                 │
     ┌──────▼──────┐   ┌──────▼──────┐   ┌───────────▼──┐   ┌──────────▼──────┐
     │  home.py    │   │ price_app   │   │volatility_app│   │  pattern_app    │
     │  (live      │   │ (LSTM       │   │ (GARCH/LSTM/ │   │  (ResNet-18     │
     │   ticker &  │   │  forecast)  │   │  Attention)  │   │   CNN image)    │
     │  heatmap)   │   └──────┬──────┘   └──────┬───────┘   └──────┬──────────┘
     └─────────────┘          │                 │                  │
                              │          ┌──────▼──────┐           │
                     ┌────────▼────┐     │ paper_app   │           │
                     │ assistant   │     │ (live paper │           │
                     │ daily_quest │     │  trading)   │           │
                     │ (Gemini Pro)│     └──────┬──────┘           │
                     └────────┬────┘            │                  │
                              │                 │                  │
                     ┌────────▼─────────────────▼──────────────────▼────┐
                     │                   Backend / Models                │
                     │  ┌─────────────┐  ┌──────────────┐  ┌──────────┐ │
                     │  │ LSTM (Keras)│  │ GARCH / LSTM │  │ResNet-18 │ │
                     │  │ price_model │  │ attn_model   │  │ (PyTorch)│ │
                     │  └─────────────┘  └──────────────┘  └──────────┘ │
                     │  ┌──────────────────────────────────────────────┐ │
                     │  │  PaperTrader engine  (paper/paper_trade.py)  │ │
                     │  └──────────────────────────────────────────────┘ │
                     └───────────────────┬───────────────────────────────┘
                                         │
                              ┌──────────▼───────────┐
                              │  yfinance · CSV data  │
                              └──────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Libraries / Services |
|---|---|
| **Data Ingestion** | `yfinance`, `pandas`, `numpy` |
| **Deep Learning** | `TensorFlow 2.13 / Keras`, `PyTorch`, `torchvision` |
| **Classical ML & Stats** | `scikit-learn 1.4`, `arch` (GARCH), `numpy 1.24` |
| **Visualisation** | `matplotlib`, `mplfinance`, `plotly` |
| **Frontend** | `streamlit`, `streamlit-autorefresh` |
| **AI / LLM** | `google-generativeai` (Gemini Pro) |
| **Image Processing** | `opencv-python`, `Pillow` |
| **Brokerage / Trading** | `alpaca-py` (Alpaca Markets SDK) |
| **Utilities** | `tqdm`, `pyyaml`, `joblib`, `pytz` |

---

## 📂 Project Structure

```
TradeSphere/
├── backend/
│   ├── agent/
│   │   ├── LSTM_model.py              # PyTorch LSTM definition for the trading agent
│   │   ├── trading_agent.py           # Core decision-making agent (BUY/SELL/HOLD)
│   │   ├── alpaca_connector.py        # Alpaca REST API wrapper (alpaca-py SDK)
│   │   ├── alpaca_stream.py           # Alpaca WebSocket data stream
│   │   ├── indicator_engine.py        # Technical indicators (RSI, SMA, MACD, BB)
│   │   ├── data_loader.py             # Market data fetcher (yfinance)
│   │   ├── auto_trade.py              # Automated trading loop
│   │   └── train_and_save_LSTM_model.py  # Agent LSTM training script
│   ├── paper/
│   │   ├── paper_trade.py         # PaperTrader engine (buy/sell/stop-loss/P&L)
│   │   ├── train_and_predict.py   # LSTM retrain + signal generation
│   │   ├── data_loader.py         # Market-state detection (live / closed)
│   │   └── model.py               # Paper trading LSTM definition
│   ├── pattern/
│   │   ├── model.py               # ResNet-18 CNN definition
│   │   ├── train.py               # Training loop (PyTorch)
│   │   ├── chart_dataset.py       # Dataset & DataLoader
│   │   ├── data_preprocessing.py
│   │   ├── image_preprocessing.py
│   │   └── label_preprocessing.py
│   ├── price/
│   │   ├── train_price_model.py   # LSTM price model training
│   │   ├── auto_trainer.py        # Scheduled auto-retraining
│   │   ├── data_loader.py
│   │   └── load_and_predict_price_model.py
│   └── volatility/
│       ├── model_lstm.py          # LSTM volatility model
│       ├── model_attention.py     # Attention-LSTM model
│       ├── model_garch.py         # GARCH(1,1) model
│       ├── compare_models.py
│       ├── evaluate_models.py
│       └── data_loader.py
├── data/
│   ├── raw/                       # Raw CSV / image data
│   └── processed/                 # Preprocessed labels & features
├── frontend/
│   ├── home.py                    # Landing page — ticker tape & sector heatmap
│   └── pages/
│       ├── price_app.py           # Price prediction dashboard
│       ├── volatility_app.py      # Volatility risk dashboard
│       ├── pattern_app.py         # Chart pattern recognition dashboard
│       ├── paper_app.py           # Live paper trading dashboard
│       ├── agent_app.py           # Alpaca automated trading agent dashboard
│       └── daily_quest.py         # Gemini-generated daily trading quests
├── models/                        # Saved model weights (organised by module)
│   ├── agent/
│   │   ├── LSTM_model.ptl
│   │   └── standard_scaler.pkl
│   ├── paper/
│   │   ├── LSTM_model.ptl
│   │   └── scaler.pkl
│   ├── pattern/
│   │   └── chart_pattern_model.pth
│   ├── price/
│   │   ├── price_model.h5
│   │   └── scaler.pkl
│   └── volatility/
│       ├── lstm_model.h5
│       └── attention_model.h5
├── outputs/
│   ├── plots/                     # Training & evaluation charts
│   └── predictions/               # Prediction CSV exports
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites

- Python **3.9** or higher
- `pip` package manager
- (Optional) NVIDIA GPU with CUDA for accelerated model training
- (Optional) A [Google Gemini API key](https://aistudio.google.com/app/apikey) for Daily Quests
- (Optional) An [Alpaca Markets API key](https://alpaca.markets) for the Automated Trading Agent

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/soham29640/TradeSphere.git
cd TradeSphere

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# 3. Install all dependencies
pip install -r requirements.txt
```

### Configure Secrets (AI Features)

Create a `.streamlit/secrets.toml` file in the project root to enable Daily Quests:

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```

> Without this key the Daily Quests page will still load but will not be able to generate challenges.

For the Automated Trading Agent, enter your Alpaca API credentials directly in the dashboard UI (or set them via environment variables `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`, and `APCA_API_BASE_URL`).

### Train the Models (optional)

Pre-trained weights can be placed directly in `models/`. To retrain from scratch:

```bash
# Price prediction model
python backend/price/train_price_model.py

# Volatility models
python backend/volatility/model_lstm.py
python backend/volatility/model_attention.py

# Chart pattern CNN (ResNet-18)
cd backend/pattern
python train.py
```

---

## 💻 Usage

### Launch the Full Platform

Start the multi-page Streamlit app from the `frontend/` directory:

```bash
streamlit run frontend/home.py
```

This opens the **Home Dashboard** at `http://localhost:8501` with navigation to all pages in the sidebar.

### Launch Individual Dashboards

You can also run any page in isolation:

```bash
# Price Prediction Dashboard
streamlit run frontend/pages/price_app.py

# Volatility Risk Dashboard
streamlit run frontend/pages/volatility_app.py

# Chart Pattern Recognition Dashboard
streamlit run frontend/pages/pattern_app.py

# Paper Trading Dashboard
streamlit run frontend/pages/paper_app.py

# Automated Trading Agent (Alpaca)
streamlit run frontend/pages/agent_app.py

# Daily Quests
streamlit run frontend/pages/daily_quest.py
```

---

### 🏠 Home Dashboard

The landing page features a live scrolling ticker tape across 15 symbols (equities, indices, crypto, commodities) and a sector heat-map showing real-time colour-coded % moves across six market sectors.

---

### 📈 Price Prediction Dashboard

1. Enter a stock ticker in the sidebar (e.g. `AAPL`, `TSLA`, `MSFT`).
2. Select a prediction horizon (5–30 steps at 5-minute intervals).
3. View the candlestick chart alongside the AI forecast overlay.
4. Monitor live **Current Price** and **Next Predicted Price** with percentage change.
5. Dashboard auto-refreshes every 3 minutes to stay in sync with the market.

---

### 📊 Volatility Risk Dashboard

1. Upload your own `returns.csv` or use the default AAPL dataset.
2. Adjust the historical lookback window using the sidebar slider.
3. Compare GARCH, LSTM, and Attention-LSTM forecasts on a single chart.
4. Receive an instant **🟢 Low Risk / 🔴 High Risk** classification against the 75th-percentile threshold.

---

### 🔍 Chart Pattern Recognition Dashboard

1. Upload a candlestick chart image (`.jpg`, `.png`, `.jpeg`) via the sidebar.
2. Instantly receive the **top 3 predicted patterns** with confidence scores.
3. Explore the confidence bar chart for a full visual breakdown.

**Supported Patterns (20 classes):**

> Ascending Triangle · Channel Down · Channel Up · Cup and Handle · Descending Triangle · Double Bottom · Double Top · Falling Wedge · Head & Shoulders · Inverse Head & Shoulders · Rectangle · Resistance Breakout · Resistance Emerging · Rising Wedge · Rounding Bottom · Rounding Top · Support Breakout · Triangle · Triple Bottom · Triple Top

---

### 💹 Paper Trading Dashboard

The paper trading module operates in two modes depending on current market hours:

| Condition | Behaviour |
|---|---|
| **Market Live** (≥ 25 min / 5 bars of today's data available) | LSTM retrains on the latest 5-min bars every 5 minutes. A **1-min trade window** opens after each retrain; trading is locked for 4 minutes between windows. Live 1-min tick chart is displayed. |
| **Market Closed** (< 25 min data or outside trading hours) | Shows the last complete session's 5-min chart. No LSTM retrain, no buy/sell panel. |

**Portfolio controls:**
- Set starting cash, stop-loss %, and maximum position size.
- Buy / Sell shares during the open trade window.
- Monitor real-time Cash, Holdings, Avg Cost, Unrealised P&L, Realised P&L, Portfolio Value, and Total Return %.
- Automatic stop-loss liquidation bypasses window locks.
- Export full trade log as a timestamped CSV.

---

### 🤖 Automated Trading Agent (Alpaca)

The Alpaca Trading Agent connects to the Alpaca Markets API to execute automated paper or live trades:

- Enter your Alpaca API credentials (Key ID and Secret) directly in the dashboard UI.
- Choose **Paper** mode (safe, simulated) or **Live** mode (real money) via the radio button.
- Configure the ticker, share quantity, and polling interval (30 s / 60 s / 120 s).
- The agent fetches live OHLCV data, computes RSI, SMA, MACD, and Bollinger Band features, and runs the pretrained LSTM to predict the next close price.
- A **BUY** signal fires when the predicted change exceeds +1 % (and cash is sufficient); a **SELL** signal fires when the predicted change falls below −1 %.
- All actions are logged in a live terminal panel inside the dashboard.
- The agent model and scaler are stored in `models/agent/`.

> **Note:** Alpaca API keys are required. Get free paper-trading keys at [alpaca.markets](https://alpaca.markets).

---

### 🎯 Daily Quests

A fresh set of Gemini-generated trading challenges is produced each day. Use them to:
- Sharpen your technical analysis skills
- Explore quantitative concepts with guided exercises
- Benchmark your market knowledge

---

## 🤖 Models

### Price Prediction — LSTM

| Property | Value |
|---|---|
| **Architecture** | 3-layer stacked LSTM (128 → 64 → 32 units) + `BatchNormalization` + `Dropout` + Dense head |
| **Input** | 60 consecutive 5-minute close prices (MinMax-scaled) |
| **Output** | Next N price steps (configurable horizon: 5–30) |
| **Training data** | 1-month 5-minute OHLCV data via `yfinance` |
| **Auto-retrain** | Daily (price dashboard) / Every 5 min during market hours (paper trading) |

---

### Volatility Forecasting — Ensemble

| Model | Description |
|---|---|
| **GARCH(1,1)** | Classical econometric model for conditional heteroskedasticity |
| **LSTM** | Sequence model trained on log returns to forecast squared returns |
| **Attention-LSTM** | LSTM augmented with a custom `AttentionSum` layer for improved temporal focus |

- **Risk classification threshold:** 75th percentile of rolling historical volatility.
- All three forecasts are rendered side-by-side for direct comparison.

---

### Chart Pattern CNN — ResNet-18

| Property | Value |
|---|---|
| **Architecture** | Pre-trained ResNet-18 with a replaced fully-connected head (20 sigmoid outputs) |
| **Training** | Transfer learning with `BCEWithLogitsLoss` and class-weighted sampling |
| **Input** | 224 × 224 RGB candlestick chart images |
| **Output** | Probability distribution over 20 chart pattern classes |

---

### Paper Trading — Online LSTM

| Property | Value |
|---|---|
| **Architecture** | Compact LSTM trained on recent intraday 5-min OHLCV bars |
| **Retrain cadence** | Every 5 minutes during market hours |
| **Trade window** | 1-minute open window → 4-minute lockout per cycle |
| **Risk controls** | Configurable stop-loss %, maximum position size cap |

---

### Trading Agent — Alpaca LSTM

| Property | Value |
|---|---|
| **Architecture** | Stacked LSTM (PyTorch) with technical indicator features |
| **Features** | Close, RSI, SMA-20, SMA-50, MACD, MACD signal, Bollinger Bands (upper/lower) |
| **Input window** | 78 bars of 1-day OHLCV + indicator data |
| **Output** | Next-bar close price prediction |
| **Signal logic** | BUY if predicted change > +1%; SELL if predicted change < −1%; HOLD otherwise |
| **Saved weights** | `models/agent/LSTM_model.ptl` · `models/agent/standard_scaler.pkl` |

---

## ⚙️ Configuration

| Setting | Location | Description |
|---|---|---|
| `GEMINI_API_KEY` | `.streamlit/secrets.toml` | Required for Daily Quests |
| `APCA_API_KEY_ID` | Agent UI / `.env` | Alpaca API key for Trading Agent |
| `APCA_API_SECRET_KEY` | Agent UI / `.env` | Alpaca API secret for Trading Agent |
| `APCA_API_BASE_URL` | Agent UI / `.env` | Alpaca base URL (paper or live) |
| Auto-refresh interval | `price_app.py` | Default: 3 minutes |
| Paper trading refresh | `paper_app.py` | Default: 5 minutes |
| Starting cash | `PaperTrader.__init__` | Default: $100,000 |
| Stop-loss % | `PaperTrader.__init__` | Default: 2% |
| Max position | `PaperTrader.__init__` | Default: 500 shares |
| Risk threshold | Volatility backend | 75th percentile rolling volatility |
| Agent signal threshold | `TradingAgent.__init__` | Default: 1% price change to trigger trade |
| Agent sanity threshold | `TradingAgent.__init__` | Default: 5% max change (guards outliers) |

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository.
2. **Create a feature branch:** `git checkout -b feature/your-feature-name`
3. **Commit your changes:** `git commit -m "feat: describe your change"`
4. **Push to your fork:** `git push origin feature/your-feature-name`
5. **Open a Pull Request** against `main`.

Please ensure your code follows the existing style, that all models still train and run correctly, and that new Streamlit pages are registered in `home.py` navigation.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/soham29640">soham29640</a></sub>
</div>
