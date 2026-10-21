# Supertrend (7, 3) flip study · 2026-10-21

1,496 stocks (sp1500), signals from 2022-01-24 to 2026-10-20. Entries are every Supertrend (7, 3) flip up, with no other filter (the chart's buy arrows alone), bought at the next day's open: 22,782 trades. Results are in **R** (multiples of the initial risk) after 0.1% slippage each way. Control: for each signal, a random stock that was tradeable the same day, with its stop the same number of ATRs below the price (at most 15%) and the same exit. Trades still open at the end are counted at the last close. Caveat: today's index members only (survivorship bias flatters long results).

## Verdict

- **Best exit: Stop only, 60 days.** +0.11R per trade, 42% winners, profit factor 1.20, held 41 days on average. The chart's own exit (Trail Supertrend (7, 3), 120 days) made +0.06R vs +0.08R on random stocks (-0.02R edge).
- **Does the stock picking help?** The same exit on random stocks bought the same days made +0.12R, so the signals add **-0.01R per trade**. Signals beat random stocks in 1 of 5 years.
- **Is it worth the time?** +0.05R per 20 days a position is held, vs +0.04R for the chart's own exit.

## All exits

`random avg R` = same exit on a random stock bought the same day. `edge R` = signals minus random.

| exit | trades | win % | avg R | median R | profit factor | avg days | R per 20 days | wins 3R plus % | random avg R | edge R |
|---|---|---|---|---|---|---|---|---|---|---|
| Trail Supertrend (7, 3), 120 days | 22,782 | 38.7 | +0.06 | -0.28 | 1.16 | 27.1 | +0.04 | 2.9 | +0.08 | -0.02 |
| Close below Supertrend (7, 3), 120 days | 22,782 | 38.8 | +0.08 | -0.31 | 1.17 | 33.5 | +0.05 | 4.0 | +0.09 | -0.02 |
| Trail Supertrend (10, 3), 120 days | 22,782 | 38.9 | +0.06 | -0.28 | 1.16 | 27.4 | +0.05 | 3.0 | +0.08 | -0.02 |
| Stop only, 60 days | 22,782 | 42.4 | +0.11 | -0.72 | 1.20 | 40.5 | +0.05 | 4.9 | +0.12 | -0.01 |
| 2R target, 20 days | 22,782 | 51.5 | +0.06 | +0.03 | 1.18 | 16.9 | +0.07 | 0.1 | +0.08 | -0.02 |
| 3R target, 40 days | 22,782 | 46.0 | +0.07 | -0.19 | 1.15 | 29.3 | +0.05 | 0.8 | +0.09 | -0.02 |
| Trail 3 ATR under highest close, 60 days | 22,782 | 39.2 | +0.06 | -0.27 | 1.15 | 24.7 | +0.05 | 2.8 | +0.07 | -0.01 |
| Close below 50-day, 120 days | 22,782 | 31.5 | +0.05 | -0.26 | 1.15 | 24.7 | +0.04 | 3.3 | +0.07 | -0.02 |
| Half at 2R, rest trails Supertrend (7, 3) | 22,782 | 38.9 | +0.06 | -0.28 | 1.16 | 27.1 | +0.04 | 1.5 | +0.08 | -0.02 |

## Best exit (Stop only, 60 days) by year

| year | trades | win % | avg R | median R | profit factor | avg days | R per 20 days | wins 3R plus % | random avg R | edge R |
|---|---|---|---|---|---|---|---|---|---|---|
| 2022 | 4,336 | 33.0 | -0.24 | -1.01 | 0.63 | 38.3 | -0.12 | 1.6 | -0.26 | +0.02 |
| 2023 | 4,645 | 48.7 | +0.30 | -0.10 | 1.60 | 43.8 | +0.14 | 5.9 | +0.30 | -0.00 |
| 2024 | 4,870 | 44.7 | +0.22 | -0.52 | 1.41 | 41.6 | +0.11 | 6.3 | +0.26 | -0.03 |
| 2025 | 5,041 | 40.2 | +0.06 | -1.01 | 1.10 | 41.5 | +0.03 | 5.0 | +0.09 | -0.04 |
| 2026 | 3,890 | 45.5 | +0.20 | -0.20 | 1.41 | 36.4 | +0.11 | 5.4 | +0.20 | -0.00 |

## Best exit by relative strength (RS) on the signal day

| rs | trades | win % | avg R | median R | profit factor | avg days | R per 20 days | wins 3R plus % |
|---|---|---|---|---|---|---|---|---|
| 1-49 | 11,232 | 41.3 | +0.06 | -1.01 | 1.11 | 40.4 | +0.03 | 4.5 |
| 50-69 | 4,917 | 43.7 | +0.14 | -0.52 | 1.25 | 40.9 | +0.07 | 4.7 |
| 70-84 | 3,437 | 44.8 | +0.17 | -0.36 | 1.34 | 41.6 | +0.08 | 4.8 |
| 85-99 | 3,196 | 41.7 | +0.17 | -1.01 | 1.30 | 39.2 | +0.08 | 6.7 |

## Best exit by market regime

| regime | trades | win % | avg R | median R | profit factor | avg days | R per 20 days | wins 3R plus % | random avg R | edge R |
|---|---|---|---|---|---|---|---|---|---|---|
| MIXED | 5,293 | 43.3 | +0.09 | -0.62 | 1.17 | 39.5 | +0.05 | 4.1 | +0.04 | +0.05 |
| RISK-OFF | 2,840 | 38.7 | -0.04 | -1.01 | 0.92 | 40.4 | -0.02 | 3.0 | -0.04 | -0.00 |
| RISK-ON | 14,649 | 42.8 | +0.15 | -0.67 | 1.27 | 40.9 | +0.07 | 5.5 | +0.18 | -0.04 |

Not financial advice. One study on past data; markets change.
