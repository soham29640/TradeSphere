from __future__ import annotations

import pandas as pd
from datetime import datetime, timezone
from typing import Optional

# ── Trading window constants ──────────────────────────────────────────────────
TRADE_WINDOW_SECONDS  = 60    # 1 minute: window is OPEN for trading
TRADE_LOCKOUT_SECONDS = 240   # 4 minutes: window is LOCKED after a trade/refresh
CYCLE_SECONDS         = TRADE_WINDOW_SECONDS + TRADE_LOCKOUT_SECONDS  # 300 s = 5 min


class PaperTrader:
    """
    Paper trading engine with:
    - 1-min open / 4-min locked trading-window cadence (aligned to 5-min refresh)
    - Running P&L (realised + unrealised)
    - Per-trade stop-loss enforcement
    - Max position size guard
    - Full trade log
    """

    def __init__(
        self,
        starting_cash: float = 100_000.0,
        stop_loss_pct: float = 2.0,       # sell if price drops > X% from avg cost
        max_position:  int   = 500,        # max shares held at once
    ):
        self.starting_cash = starting_cash
        self.cash          = starting_cash
        self.holdings      = 0.0
        self.avg_cost      = 0.0           # weighted average cost basis
        self.stop_loss_pct = stop_loss_pct
        self.max_position  = max_position
        self.realised_pnl  = 0.0

        # Trading-window state
        self._window_start: Optional[datetime] = None   # UTC time window opened
        self._trades: list[dict] = []

    # ── Trading window logic ──────────────────────────────────────────────────

    def open_trading_window(self):
        """
        Call once per 5-min refresh cycle.
        Opens a 1-min window; after TRADE_WINDOW_SECONDS it auto-locks.
        """
        self._window_start = datetime.now(timezone.utc)

    def is_window_open(self) -> tuple[bool, int]:
        """
        Returns (open: bool, seconds_remaining: int).
        Window is open for the first TRADE_WINDOW_SECONDS of each cycle.
        """
        if self._window_start is None:
            return False, 0
        elapsed = (datetime.now(timezone.utc) - self._window_start).total_seconds()
        if elapsed <= TRADE_WINDOW_SECONDS:
            remaining = int(TRADE_WINDOW_SECONDS - elapsed)
            return True, remaining
        # Locked phase
        lock_remaining = int(CYCLE_SECONDS - elapsed)
        return False, max(0, lock_remaining)

    def window_status_str(self) -> str:
        """Human-readable window status for the UI."""
        open_, secs = self.is_window_open()
        if self._window_start is None:
            return "⏳ Waiting for first refresh"
        if open_:
            return f"🟢 TRADE WINDOW OPEN — {secs}s remaining"
        return f"🔒 LOCKED — next window in ~{secs}s"

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _log(self, action: str, price: float, qty: float, timestamp: str, note: str = ""):
        self._trades.append(
            dict(
                Timestamp   = timestamp,
                Action      = action,
                Price       = round(price, 4),
                Quantity    = qty,
                Cash        = round(self.cash, 2),
                Holdings    = round(self.holdings, 4),
                AvgCost     = round(self.avg_cost, 4),
                RealisedPnL = round(self.realised_pnl, 2),
                Note        = note,
            )
        )

    def _check_window(self) -> Optional[str]:
        """Return an error string if the trading window is closed, else None."""
        open_, secs = self.is_window_open()
        if not open_:
            return f"🔒 Trading locked — window opens in ~{secs}s"
        return None

    # ── Public API ────────────────────────────────────────────────────────────
    def buy(
        self,
        price: float,
        quantity: float,
        timestamp: Optional[str] = None,
        bypass_window: bool = False,        # True for stop-loss auto-sells
    ) -> str:
        timestamp = timestamp or datetime.now().isoformat(timespec="seconds")
        quantity  = float(quantity)

        if not bypass_window:
            err = self._check_window()
            if err:
                return err

        if quantity <= 0:
            return "❌ Quantity must be positive."
        if self.holdings + quantity > self.max_position:
            return f"❌ Exceeds max position ({self.max_position} shares)."

        cost = price * quantity
        if self.cash < cost:
            return f"❌ Insufficient cash (need ${cost:.2f}, have ${self.cash:.2f})."

        total_held    = self.holdings * self.avg_cost + cost
        self.holdings += quantity
        self.avg_cost  = total_held / self.holdings if self.holdings else 0.0
        self.cash     -= cost

        self._log("BUY", price, quantity, timestamp)
        return f"✅ Bought {quantity:.0f} @ ${price:.2f}"

    def sell(
        self,
        price: float,
        quantity: float,
        timestamp: Optional[str] = None,
        bypass_window: bool = False,
    ) -> str:
        timestamp = timestamp or datetime.now().isoformat(timespec="seconds")
        quantity  = float(quantity)

        if not bypass_window:
            err = self._check_window()
            if err:
                return err

        if quantity <= 0:
            return "❌ Quantity must be positive."
        if self.holdings < quantity:
            return f"❌ Not enough holdings ({self.holdings:.0f} held)."

        revenue           = price * quantity
        cost_basis        = self.avg_cost * quantity
        trade_pnl         = revenue - cost_basis
        self.realised_pnl += trade_pnl
        self.cash         += revenue
        self.holdings     -= quantity

        if self.holdings == 0:
            self.avg_cost = 0.0

        self._log("SELL", price, quantity, timestamp, note=f"P&L {trade_pnl:+.2f}")
        return f"✅ Sold {quantity:.0f} @ ${price:.2f}  |  Trade P&L: ${trade_pnl:+.2f}"

    def check_stop_loss(self, current_price: float, timestamp: Optional[str] = None) -> str | None:
        """
        If current_price has dropped > stop_loss_pct below avg cost, liquidate.
        Bypasses trading window — stop-loss always executes.
        """
        if self.holdings <= 0 or self.avg_cost <= 0:
            return None
        drop_pct = (self.avg_cost - current_price) / self.avg_cost * 100
        if drop_pct >= self.stop_loss_pct:
            msg = self.sell(current_price, self.holdings, timestamp, bypass_window=True)
            return f"🛑 Stop-loss triggered ({drop_pct:.2f}% drop): {msg}"
        return None

    # ── Portfolio metrics ─────────────────────────────────────────────────────
    def portfolio_value(self, current_price: float) -> float:
        return self.cash + self.holdings * current_price

    def unrealised_pnl(self, current_price: float) -> float:
        if self.holdings <= 0:
            return 0.0
        return self.holdings * (current_price - self.avg_cost)

    def total_return_pct(self, current_price: float) -> float:
        value = self.portfolio_value(current_price)
        return (value - self.starting_cash) / self.starting_cash * 100

    def status(self, current_price: float) -> dict:
        pv = self.portfolio_value(current_price)
        return {
            "Cash":            round(self.cash, 2),
            "Holdings":        round(self.holdings, 4),
            "Avg Cost":        round(self.avg_cost, 4),
            "Current Price":   round(current_price, 4),
            "Portfolio Value": round(pv, 2),
            "Unrealised P&L":  round(self.unrealised_pnl(current_price), 2),
            "Realised P&L":    round(self.realised_pnl, 2),
            "Total Return %":  round(self.total_return_pct(current_price), 3),
        }

    def get_trade_dataframe(self) -> pd.DataFrame:
        cols = ["Timestamp", "Action", "Price", "Quantity",
                "Cash", "Holdings", "AvgCost", "RealisedPnL", "Note"]
        return pd.DataFrame(self._trades, columns=cols)

    def reset(self):
        """Reset portfolio to initial state (keeps stop-loss / max-position settings)."""
        self.__init__(
            starting_cash=self.starting_cash,
            stop_loss_pct=self.stop_loss_pct,
            max_position=self.max_position,
        )