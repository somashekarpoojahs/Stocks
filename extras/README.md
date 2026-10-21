# Extras: earlier one-off tools (20 Oct 2026)

These were built before the Smart Scanner and are kept for reference. For daily stock picks, use
`smart_scanner/` (see the main README). They use only the Python standard library.

- **`signals.py`** checks technical signals for the options spread system:
  - BULLISH: close > SMA50 > SMA100, RSI 45–70, MACD histogram > 0 or rising.
  - BEARISH: the mirror image.
  - Anything else is NO TRADE.

  It takes a JSON of daily closes plus the last 15 highs and lows per ticker, and writes `signals.json`.
  Run it with `python extras/signals.py prices.json`. The rules are in `docs/options-spread-system.md`.
- **`tenx.py`** is the "10x" earnings-option screen. For each option it works out how far the stock must
  move by expiry for the option to be worth 10× its ask. It compares that with the options-implied move
  and the stock's average earnings move. The quotes are a 20 Oct 2026 snapshot written into the file.
  Run it with `python extras/tenx.py`.
- **`trendstart.py`** was the first trend-start scanner. It scores a 10-point checklist built on
  Supertrend, a 50-day breakout, a volume surge, RSI, and strength vs SPY. It takes a JSON of daily bars
  per ticker plus SPY. Run it with `python extras/trendstart.py bars.json`. The notes and results are in
  `docs/trend-start-scanner.md`.
