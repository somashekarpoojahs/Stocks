# Trend-start stock scanner (first version)

> Notes from 20 Oct 2026, superseded by the Smart Scanner in `smart_scanner/` (many more indicators, scoring, regime filter, trade plans, backtest). Kept for reference.

Goal: find stocks that look like they are *starting* a strong uptrend, not ones that already ran a long way. Code: `extras/trendstart.py` (daily bars per ticker + SPY).

## Rules (one point each)
1. Supertrend(10, 3) in an up trend
2. Supertrend flipped up within the last 10 days (fresh trend)
3. New 50-day closing high within the last 3 days (breakout)
4. Volume surge: biggest day in last 5 >= 1.5x prior 50-day average
5. Close > 20-day average > 50-day average
6. RSI(14) 55-75 (above 80 = stretched, minus 1)
7. Less than 20% above 50-day average (above 40% = minus 1)
8. Beat SPY over the last ~3 months
9. Up less than 60% over ~3 months (otherwise MATURE)
10. Today's candle closes in the top 30% of its range (+0.5)
Flags: PINNED (tiny daily range, e.g. takeover), MATURE, STRETCHED.
The Supertrend line doubles as the "trend is broken" level.

## How to cover 1,000+ stocks
Claude's workspace can't bulk-download prices, and IBKR returns one stock per call. Funnel: market-wide screen (IBKR saved screener, or daily new-high / top-gainer lists) -> top ~50 -> trendstart.py on IBKR daily bars -> earnings/news check.

## Scan 20 Oct 2026 (intraday, ~20:00 Irish time)
Universe: Trefis new 52-week-high lists (19 Oct) and top 1-month gainers. SPY +3.8% over the window.

| Ticker | Score | Read | Supertrend line | Earnings |
|---|---|---|---|---|
| MTCH | 8.5 | Fresh trend start: Supertrend flipped up 3 days ago, broke 3-month range to new high, RSI 71, +18% in 3 months | $41.45 (-10.5%) | 2 Nov after close |
| CLF | 8.5 | Post-earnings breakout: +16% on 19 Oct on ~6.5x volume after best quarter in 3 years | $11.23 (-18%) | Reported 19 Oct |
| VEEV | 8.0 | Established uptrend at new highs, +57% in 3 months, RSI 73 | $285.16 (-9.6%) | Not in next few weeks (not verified) |
| PAYC | 7.5 | Breakout but RSI 79, MATURE | $237.75 | Not checked |
| MCK | 7.5 | Steady new highs, RSI 78 | $951.95 | Not checked |
| TTAN | 4.5 | Recovering after Sept crash, below old highs | $68.69 | - |
| MRNA | 4.5 | Already ran ~4x in 2 months (+177% on 19 Aug), 50% above 50-day: MATURE, STRETCHED | $179.92 | - |
| GRAL | 1.5 | Supertrend turned down | - | - |
