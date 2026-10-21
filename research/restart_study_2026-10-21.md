# Trend-restart study · 2026-10-21

1,496 stocks (sp1500), signals from 2022-09-08 to 2026-10-20. Entries are trend restarts: the Supertrend (7, 3) flips up after a pullback of 8%+ (RSI(14) dipped to 40) in a stock with a rising 200-day average, within 25% of its 52-week high, bought at the next day's open: 5,777 trades. Results are in **R** (multiples of the initial risk) after 0.1% slippage each way. Control: for each signal, a random stock that was tradeable the same day, with its stop the same number of ATRs below the price (at most 15%) and the same exit. Trades still open at the end are counted at the last close. Caveat: today's index members only (survivorship bias flatters long results).

## Verdict

- **Best exit: Stop only, 60 days.** +0.22R per trade, 46% winners, profit factor 1.43, held 41 days on average. The chart's own exit (Trail Supertrend (7, 3), 120 days) made +0.10R vs +0.13R on random stocks (-0.03R edge).
- **Does the stock picking help?** The same exit on random stocks bought the same days made +0.21R, so the signals add **+0.01R per trade**. Signals beat random stocks in 2 of 5 years.
- **Is it worth the time?** +0.11R per 20 days a position is held, vs +0.07R for the chart's own exit.

## All exits

`random avg R` = same exit on a random stock bought the same day. `edge R` = signals minus random.

| exit | trades | win % | avg R | median R | profit factor | avg days | R per 20 days | wins 3R plus % | random avg R | edge R |
|---|---|---|---|---|---|---|---|---|---|---|
| Trail Supertrend (7, 3), 120 days | 5,777 | 39.9 | +0.10 | -0.26 | 1.26 | 27.3 | +0.07 | 3.1 | +0.13 | -0.03 |
| Close below Supertrend (7, 3), 120 days | 5,777 | 39.8 | +0.13 | -0.29 | 1.30 | 34.2 | +0.07 | 4.5 | +0.15 | -0.02 |
| Trail Supertrend (10, 3), 120 days | 5,777 | 40.0 | +0.10 | -0.26 | 1.26 | 27.6 | +0.07 | 3.1 | +0.13 | -0.03 |
| Stop only, 60 days | 5,777 | 46.2 | +0.22 | -0.28 | 1.43 | 40.9 | +0.11 | 5.8 | +0.21 | +0.01 |
| 2R target, 20 days | 5,777 | 51.8 | +0.07 | +0.04 | 1.20 | 16.9 | +0.08 | 0.1 | +0.10 | -0.02 |
| 3R target, 40 days | 5,777 | 47.7 | +0.14 | -0.10 | 1.29 | 29.2 | +0.09 | 0.9 | +0.14 | -0.00 |
| Trail 3 ATR under highest close, 60 days | 5,777 | 40.5 | +0.10 | -0.24 | 1.28 | 25.0 | +0.08 | 3.1 | +0.11 | -0.01 |
| Close below 50-day, 120 days | 5,777 | 31.9 | +0.10 | -0.24 | 1.30 | 25.1 | +0.08 | 3.7 | +0.10 | -0.01 |
| Half at 2R, rest trails Supertrend (7, 3) | 5,777 | 40.1 | +0.10 | -0.26 | 1.27 | 27.3 | +0.07 | 1.4 | +0.11 | -0.01 |

## Best exit (Stop only, 60 days) by year

| year | trades | win % | avg R | median R | profit factor | avg days | R per 20 days | wins 3R plus % | random avg R | edge R |
|---|---|---|---|---|---|---|---|---|---|---|
| 2022 | 194 | 52.6 | +0.20 | +0.12 | 1.52 | 47.6 | +0.08 | 1.0 | +0.35 | -0.15 |
| 2023 | 1,281 | 51.7 | +0.45 | +0.18 | 1.94 | 43.8 | +0.20 | 7.3 | +0.30 | +0.14 |
| 2024 | 1,705 | 47.2 | +0.28 | -0.32 | 1.52 | 41.9 | +0.13 | 7.2 | +0.24 | +0.03 |
| 2025 | 1,330 | 36.1 | -0.08 | -1.02 | 0.87 | 39.3 | -0.04 | 4.1 | -0.05 | -0.03 |
| 2026 | 1,267 | 49.0 | +0.25 | -0.04 | 1.57 | 37.4 | +0.13 | 4.8 | +0.33 | -0.07 |

## Best exit by relative strength (RS) on the signal day

| rs | trades | win % | avg R | median R | profit factor | avg days | R per 20 days | wins 3R plus % |
|---|---|---|---|---|---|---|---|---|
| 1-49 | 1,125 | 41.1 | +0.06 | -1.01 | 1.11 | 39.6 | +0.03 | 5.1 |
| 50-69 | 1,802 | 47.6 | +0.26 | -0.18 | 1.51 | 40.7 | +0.13 | 5.9 |
| 70-84 | 1,533 | 48.3 | +0.28 | -0.13 | 1.57 | 42.3 | +0.13 | 5.2 |
| 85-99 | 1,317 | 46.3 | +0.25 | -0.21 | 1.49 | 40.7 | +0.12 | 6.8 |

## Best exit by market regime

| regime | trades | win % | avg R | median R | profit factor | avg days | R per 20 days | wins 3R plus % | random avg R | edge R |
|---|---|---|---|---|---|---|---|---|---|---|
| MIXED | 1,138 | 50.0 | +0.30 | -0.00 | 1.65 | 39.8 | +0.15 | 5.6 | +0.27 | +0.03 |
| RISK-OFF | 297 | 60.9 | +0.47 | +0.47 | 2.47 | 49.2 | +0.19 | 4.0 | +0.62 | -0.15 |
| RISK-ON | 4,342 | 44.2 | +0.19 | -0.62 | 1.34 | 40.6 | +0.09 | 5.9 | +0.17 | +0.02 |

Not financial advice. One study on past data; markets change.
