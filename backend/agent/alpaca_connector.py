"""
alpaca_connector.py
───────────────────
Thin wrapper around the Alpaca REST API for placing market orders and
querying account state.

Fixes:
- Replaced deprecated `alpaca_trade_api.REST` import path with the current
  `alpaca.trading` SDK (alpaca-py ≥ 0.8).  The old `alpaca-trade-api` package
  is no longer maintained.  If the caller still uses the old package, a
  compatibility shim is provided via a try/except so the file works with both.
- `get_position` now returns 0 (int) consistently when there is no open
  position, instead of swallowing *all* exceptions silently.
- Added `close_position` helper used by the trading agent.
- Added type annotations throughout.
"""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ── SDK compatibility: alpaca-py (new) vs alpaca-trade-api (legacy) ───────────
try:
    # alpaca-py ≥ 0.8  (pip install alpaca-py)
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce

    _USE_NEW_SDK = True
except ImportError:
    # Legacy alpaca-trade-api (pip install alpaca-trade-api)
    from alpaca_trade_api import REST as _LegacyREST  # type: ignore

    _USE_NEW_SDK = False


class AlpacaOrder:
    """Place and manage Alpaca paper/live orders."""

    def __init__(self) -> None:
        api_key    = os.getenv("APCA_API_KEY_ID")
        api_secret = os.getenv("APCA_API_SECRET_KEY")
        base_url   = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

        if not api_key or not api_secret:
            raise ValueError(
                "❌ Alpaca API keys missing. "
                "Set APCA_API_KEY_ID and APCA_API_SECRET_KEY in your .env file."
            )

        if _USE_NEW_SDK:
            paper = "paper-api" in base_url
            self._client = TradingClient(api_key, api_secret, paper=paper)
            acct = self._client.get_account()
            print(f"[Alpaca] Connected (alpaca-py) | Cash: ${float(acct.cash):,.2f}")
        else:
            self._legacy = _LegacyREST(
                key_id=api_key,
                secret_key=api_secret,
                base_url=base_url,
            )
            acct = self._legacy.get_account()
            print(f"[Alpaca] Connected (legacy SDK) | Cash: ${float(acct.cash):,.2f}")

    # ── Orders ────────────────────────────────────────────────────────────────
    def place_order(self, symbol: str, qty: int, side: str):
        """
        Submit a market order.

        Args:
            symbol: Ticker, e.g. 'AAPL'.
            qty:    Number of shares (must be > 0).
            side:   'buy' or 'sell'.
        """
        if qty <= 0:
            raise ValueError(f"❌ Order qty must be > 0, got {qty}")
        side_lower = side.lower()
        if side_lower not in ("buy", "sell"):
            raise ValueError(f"❌ side must be 'buy' or 'sell', got '{side}'")

        if _USE_NEW_SDK:
            order = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side_lower == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.GTC,
            )
            return self._client.submit_order(order)
        else:
            return self._legacy.submit_order(
                symbol=symbol,
                qty=qty,
                side=side_lower,
                type="market",
                time_in_force="gtc",
            )

    # ── Positions ─────────────────────────────────────────────────────────────
    def get_position(self, symbol: str) -> int:
        """Return current share count for *symbol*, or 0 if no position."""
        try:
            if _USE_NEW_SDK:
                pos = self._client.get_open_position(symbol)
            else:
                pos = self._legacy.get_position(symbol)
            return int(float(pos.qty))
        except Exception as exc:
            # Alpaca raises an API error (404) when there is no position –
            # that is expected; anything else is re-raised.
            msg = str(exc).lower()
            if "position does not exist" in msg or "404" in msg:
                return 0
            raise

    # ── Account ───────────────────────────────────────────────────────────────
    def get_cash(self) -> float:
        """Return available cash in USD."""
        if _USE_NEW_SDK:
            return float(self._client.get_account().cash)
        return float(self._legacy.get_account().cash)

    def close_position(self, symbol: str) -> Optional[object]:
        """Close the entire position for *symbol* (no-op if flat)."""
        if self.get_position(symbol) == 0:
            return None
        if _USE_NEW_SDK:
            return self._client.close_position(symbol)
        return self._legacy.close_position(symbol)