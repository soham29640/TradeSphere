"""
auto_trade.py
─────────────
Headless trading loop.  Can be imported by app.py or run directly.

Fixes:
- `log()` opened the log file twice per call (once to append, once to check
  length).  Now uses a single open in 'a+' mode to read and write in one shot.
- File trim used `f.readlines()` then re-opened for write; replaced with a
  safe atomic pattern (read → truncate → write).
- `stop_event` check was at the top of `while True:` but used `break` – the
  `while` condition now uses `stop_event` directly to be idiomatic.
- `error_count` reset only on success but was not reset on a clean stop;
  moved reset inside the try block correctly.
- Removed the bare `except: pass` in `log()`; log-rotation errors now print
  a warning instead of being silently swallowed.
- Added type annotations and docstrings.
"""

import queue
import time
from datetime import datetime
from threading import Event
from typing import Optional

from src.agents.trading_agent import TradingAgent

LOG_FILE   = "trade_log.txt"
MAX_ERRORS = 5
LOG_MAXLINES = 1000
LOG_KEEPLINES = 500

# Shared queue – used by app.py to consume log messages for the UI
log_queue: queue.Queue = queue.Queue()


# ── Logging ───────────────────────────────────────────────────────────────────
def log(msg: str) -> None:
    """Print *msg*, persist it to LOG_FILE, and push it onto log_queue."""
    print(msg)
    log_queue.put(msg)

    try:
        # Read existing content + append new line in one open
        with open(LOG_FILE, "a+", encoding="utf-8") as f:
            f.write(msg + "\n")
            f.seek(0)
            lines = f.readlines()

        # Trim if the file has grown too large
        if len(lines) > LOG_MAXLINES:
            kept = lines[-LOG_KEEPLINES:]
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.writelines(kept)

    except OSError as exc:
        print(f"⚠️  Could not write to log file: {exc}")


# ── Main loop ─────────────────────────────────────────────────────────────────
def main(
    ticker: str = "AAPL",
    qty: int = 50,
    interval: int = 60,
    stop_event: Optional[Event] = None,
) -> None:
    """
    Run the auto-trading loop.

    Args:
        ticker:      Stock ticker to trade.
        qty:         Number of shares per order.
        interval:    Seconds between each decision cycle.
        stop_event:  threading.Event; loop exits when it is set.
    """
    agent = TradingAgent(ticker)
    log(f"🔁  Auto Trading Agent started for {ticker} (interval={interval}s, qty={qty})")

    error_count = 0

    while stop_event is None or not stop_event.is_set():
        now = datetime.now()

        try:
            action, current, predicted = agent.act(qty=qty)
            error_count = 0  # reset streak on success

            if current is not None and predicted is not None:
                msg = (
                    f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"Action: {action} | Current: ${current:.2f} | Predicted: ${predicted:.2f}"
                )
            else:
                msg = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Action: {action}"

            log(msg)

        except Exception as exc:
            error_count += 1
            log(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] ❌ Error ({error_count}/{MAX_ERRORS}): {exc}")

            if error_count >= MAX_ERRORS:
                log("❌  Too many consecutive errors – stopping bot.")
                break

        # Respect stop_event during the sleep so the loop exits promptly
        deadline = time.monotonic() + interval
        while time.monotonic() < deadline:
            if stop_event and stop_event.is_set():
                break
            time.sleep(0.5)

    log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🛑  Agent stopped.")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()