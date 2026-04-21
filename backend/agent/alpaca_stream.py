"""
alpaca_stream.py
────────────────
Subscribe to Alpaca trade-update events via WebSocket.

Fixes:
- `Stream` constructor must receive keyword arguments for `data_feed`.
  Passing it as the fourth positional arg was broken in newer SDK versions.
- `base_url` should NOT be passed to `Stream` when using alpaca-py; the new
  SDK derives the WebSocket URL from the `paper` flag on `TradingStream`.
- Provided both a legacy (alpaca-trade-api) and new (alpaca-py) path.
- Added graceful KeyboardInterrupt handling so Ctrl-C exits cleanly.
- `API_KEY` / `API_SECRET` are validated before attempting connection.
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

API_KEY    = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")
BASE_URL   = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

if not API_KEY or not API_SECRET:
    raise RuntimeError(
        "❌ APCA_API_KEY_ID and APCA_API_SECRET_KEY must be set in your .env file."
    )

# ── SDK compatibility ─────────────────────────────────────────────────────────
try:
    # alpaca-py ≥ 0.8
    from alpaca.trading.stream import TradingStream

    _USE_NEW_SDK = True
except ImportError:
    # Legacy alpaca-trade-api
    from alpaca_trade_api.stream import Stream as _LegacyStream  # type: ignore

    _USE_NEW_SDK = False


# ── Handlers ──────────────────────────────────────────────────────────────────
async def handle_trade_update(data) -> None:
    """Called for every order / fill event on the account."""
    event  = getattr(data, "event",  data)
    order  = getattr(data, "order",  None)
    symbol = getattr(order, "symbol", "N/A") if order else "N/A"
    qty    = getattr(order, "qty",    "?")   if order else "?"
    print(f"🔔 Trade update | event={event} | symbol={symbol} | qty={qty}")


# ── Stream setup ──────────────────────────────────────────────────────────────
def build_stream():
    if _USE_NEW_SDK:
        paper  = "paper-api" in BASE_URL
        stream = TradingStream(API_KEY, API_SECRET, paper=paper)
        stream.subscribe_trade_updates(handle_trade_update)
        return stream
    else:
        stream = _LegacyStream(
            API_KEY,
            API_SECRET,
            base_url=BASE_URL,
            data_feed="iex",
        )

        @stream.on_trade_updates
        async def _handler(data):
            await handle_trade_update(data)

        return stream


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("📡  Starting Alpaca trade stream …  (Ctrl-C to stop)")
    stream = build_stream()
    try:
        stream.run()
    except KeyboardInterrupt:
        print("\n🛑  Stream stopped by user.")