# 🌐 TradeSphere

> **An AI-powered stock market analysis platform** combining price prediction, volatility forecasting, and chart pattern recognition — all in one interactive dashboard.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?logo=streamlit)](https://streamlit.io/)
[![PyTorch](https://img.shields.io/badge/PyTorch-CNN-orange?logo=pytorch)](https://pytorch.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-LSTM-yellow?logo=tensorflow)](https://www.tensorflow.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Usage](#-usage)
- [Models](#-models)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔭 Overview

TradeSphere is a modular machine learning platform for stock market intelligence. It provides three independent analytical engines — each with its own trained model and Streamlit dashboard — that together give traders and analysts a 360° view of market behaviour:

| Module | Task | Algorithm |
|---|---|---|
| **Price Prediction** | Forecast next N price steps | Multi-layer LSTM (TensorFlow/Keras) |
| **Volatility Forecast** | Estimate next-day risk | GARCH · LSTM · Attention-LSTM |
| **Pattern Detection** | Identify chart patterns in images | ResNet-18 CNN (PyTorch) |

---

## ✨ Features

- 📈 **Real-Time Price Prediction** — Fetches live 5-minute OHLCV data via `yfinance`, scales it with `MinMaxScaler`, and runs a deep 3-layer LSTM to predict the next 5–30 price steps, rendered as an interactive Plotly chart.
- 📊 **Volatility Risk Dashboard** — Computes next-day volatility with three competing models (GARCH, LSTM, Attention-LSTM) and classifies each forecast as 🟢 Low Risk or 🔴 High Risk against the rolling 75th-percentile threshold.
- 🔍 **Chart Pattern Recognition** — Upload any candlestick chart image and get the top-3 pattern predictions (confidence %) from a fine-tuned ResNet-18 model trained on 20 pattern classes.
- ⚡ **Auto-refresh Dashboard** — The price dashboard auto-refreshes every 3 minutes to stay in sync with the market without hammering the API.
- 📤 **Custom Data Upload** — The volatility dashboard accepts a user-uploaded `returns.csv` so you can analyse any asset, not just the defaults.

---

## 🏗 Architecture

```
User
 │
 ▼
┌─────────────────────────────────────────────────────┐
│                  Streamlit Frontend                 │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │
│  │  price_app   │ │volatility_app│ │ pattern_app │ │
│  └──────┬───────┘ └──────┬───────┘ └──────┬──────┘ │
└─────────┼────────────────┼────────────────┼─────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────┐
│                    Backend / Models                 │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │
│  │ LSTM (Keras) │ │ GARCH / LSTM │ │ ResNet-18   │ │
│  │ price_model  │ │ attn model   │ │ CNN (torch) │ │
│  └──────────────┘ └──────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────┘
          │
          ▼
    yfinance / CSV data sources
```

---

## 🛠 Tech Stack

| Layer | Libraries |
|---|---|
| **Data** | `yfinance`, `pandas`, `numpy` |
| **ML — Deep Learning** | `TensorFlow / Keras`, `PyTorch`, `torchvision` |
| **ML — Classical** | `scikit-learn`, `arch` (GARCH) |
| **Visualisation** | `matplotlib`, `mplfinance`, `plotly` |
| **Frontend** | `streamlit`, `streamlit-autorefresh` |
| **Utilities** | `opencv-python`, `Pillow`, `tqdm`, `pyyaml`, `joblib` |

---

## 📂 Project Structure

```
TradeSphere/
├── backend/
│   ├── pattern/
│   │   ├── model.py               # ResNet-18 CNN definition
│   │   ├── train.py               # Training loop (PyTorch)
│   │   ├── chart_dataset.py       # Dataset & DataLoader
│   │   ├── data_preprocessing.py
│   │   ├── image_preprocessing.py
│   │   └── label_preprocessing.py
│   ├── price/
│   │   ├── train_price_model.py   # LSTM price model training
│   │   ├── auto_trainer.py
│   │   ├── data_loader.py
│   │   └── load_and_predict_price_model.py
│   └── volatility/
│       ├── model_lstm.py          # LSTM volatility model
│       ├── model_attention.py     # Attention-LSTM model
│       ├── model_garch.py         # GARCH model
│       ├── compare_models.py
│       ├── evaluate_models.py
│       └── data_loader.py
├── data/
│   ├── raw/                       # Raw CSV data (e.g. AAPL.csv)
│   └── processed/                 # Preprocessed labels & features
├── frontend/
│   └── pages/
│       ├── price_app.py           # Price prediction dashboard
│       ├── volatility_app.py      # Volatility risk dashboard
│       └── pattern_app.py         # Chart pattern dashboard
├── models/                        # Saved model weights
│   ├── price_model.h5
│   ├── scaler.pkl
│   ├── lstm_model.h5
│   ├── attention_model.h5
│   └── chart_pattern_model.pth
├── outputs/
│   ├── plots/                     # Training & evaluation charts
│   └── predictions/               # Prediction CSV exports
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- `pip` package manager
- (Optional) NVIDIA GPU with CUDA for faster model training

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/soham29640/TradeSphere.git
cd TradeSphere

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

### Train the Models (optional)

> Pre-trained weights can be placed directly in `models/`. If you want to retrain from scratch:

```bash
# Price prediction model
python backend/price/train_price_model.py

# Volatility models (LSTM, Attention-LSTM)
python backend/volatility/model_lstm.py
python backend/volatility/model_attention.py

# Chart pattern CNN
cd backend/pattern
python train.py
```

---

## 💻 Usage

Launch any of the three Streamlit dashboards:

```bash
# Price Prediction Dashboard
streamlit run frontend/pages/price_app.py

# Volatility Risk Dashboard
streamlit run frontend/pages/volatility_app.py

# Chart Pattern Recognition Dashboard
streamlit run frontend/pages/pattern_app.py
```

Open the URL shown in your terminal (default: `http://localhost:8501`).

### Price Prediction Dashboard

1. Enter a stock ticker in the sidebar (e.g. `AAPL`, `TSLA`, `MSFT`).
2. Select a prediction horizon (5–30 steps at 5-minute intervals).
3. View the candlestick chart alongside the AI forecast.
4. Monitor live **Current Price** and **Next Predicted Price** with percentage change.

### Volatility Risk Dashboard

1. Upload your own `returns.csv` or use the default AAPL data.
2. Adjust the number of historical days using the sidebar slider.
3. Compare GARCH, LSTM, and Attention-LSTM forecasts on a single chart.
4. Receive an instant **🟢 Low Risk / 🔴 High Risk** classification.

### Chart Pattern Recognition Dashboard

1. Upload a candlestick chart image (`.jpg`, `.png`, `.jpeg`) via the sidebar.
2. Instantly receive the **top 3 predicted patterns** with confidence scores.
3. Explore the confidence bar chart for a visual breakdown.

**Supported Patterns (20 classes):**

> Ascending Triangle · Channel Down · Channel Up · Cup and Handle · Descending Triangle · Double Bottom · Double Top · Falling Wedge · Head & Shoulders · Inverse Head & Shoulders · Resistance Emerging · Resistance Breakout · Rising Wedge · Rounding Bottom · Rounding Top · Support Breakout · Triangle · Triple Bottom · Triple Top · Rectangle

---

## 🤖 Models

### Price Prediction (LSTM)
- **Architecture:** 3-layer stacked LSTM (128 → 64 → 32 units) with `BatchNormalization` and `Dropout`, followed by Dense layers.
- **Input:** 60 consecutive 5-minute close prices (MinMax-scaled).
- **Output:** Next N price steps.
- **Training data:** 1-month 5-minute OHLCV data via `yfinance`.

### Volatility Forecasting
| Model | Description |
|---|---|
| **GARCH(1,1)** | Classical econometric model for conditional heteroskedasticity |
| **LSTM** | Sequence model trained on log returns to predict squared returns |
| **Attention-LSTM** | LSTM augmented with a custom `AttentionSum` layer for improved temporal focus |

- **Risk threshold:** 75th percentile of rolling historical volatility.

### Chart Pattern CNN (ResNet-18)
- **Architecture:** Pre-trained ResNet-18 with a replaced fully-connected head (20 outputs).
- **Training:** Transfer learning with `BCEWithLogitsLoss` and class-weighted sampling.
- **Input:** 224×224 RGB candlestick chart images.
- **Output:** Probability distribution over 20 chart pattern classes.

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to your fork: `git push origin feature/your-feature-name`
5. Open a Pull Request.

Please make sure your code follows the existing code style and that all models still train and run correctly.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/soham29640">soham29640</a></sub>
</div>
