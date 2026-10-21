# Exit study · 2026-10-21

1,496 stocks (sp1500), signals from 2022-03-18 to 2026-10-19. Entries are the scanner's own signals (score ≥ 70 with a setup trigger), bought at the next day's open: 44,401 trades. Results are in **R** (multiples of the initial risk) after 0.1% slippage each way. Control: for each signal, a random stock that was tradeable the same day, with the same exit. Trades still open at the end are counted at the last close. Caveat: today's index members only (survivorship bias flatters long results).

## Verdict

- **Best exit: Stop only, 60 days.** +0.13R per trade, 28% winners, profit factor 1.17, held 28 days on average. The scanner's current exit (2R target, 20 days) made +0.01R.
- **Does the stock picking help?** The same exit on random stocks bought the same days made +0.14R, so the signals add **-0.01R per trade**. Signals beat random stocks in 2 of 5 years.
- **Is it worth the time?** +0.10R per 20 days a position is held, vs +0.02R for the current exit.

## All exits

`random avg R` = same exit on a random stock bought the same day. `edge R` = signals minus random.

| exit | trades | win % | avg R | median R | profit factor | avg days | R per 20 days | wins 3R plus % | random avg R | edge R |
|---|---|---|---|---|---|---|---|---|---|---|
| 2R target, 20 days | 44,401 | 41.7 | +0.01 | -1.02 | 1.02 | 11.7 | +0.02 | 0.5 | +0.03 | -0.02 |
| 3R target, 40 days | 44,401 | 33.6 | +0.05 | -1.03 | 1.06 | 18.0 | +0.05 | 2.5 | +0.07 | -0.02 |
| Stop only, 60 days | 44,401 | 27.9 | +0.13 | -1.03 | 1.17 | 27.7 | +0.10 | 12.6 | +0.14 | -0.01 |
| Trail 3 ATR under highest close, 60 days | 44,401 | 31.6 | +0.02 | -0.83 | 1.03 | 19.6 | +0.02 | 7.2 | +0.06 | -0.04 |
| Trail Supertrend, 120 days | 44,401 | 31.0 | +0.02 | -0.83 | 1.03 | 21.0 | +0.02 | 6.8 | +0.06 | -0.04 |
| Close below 21-EMA, 60 days | 44,401 | 31.1 | +0.01 | -0.40 | 1.02 | 13.4 | +0.01 | 4.7 | +0.01 | +0.00 |
| Close below 50-day, 120 days | 44,401 | 27.6 | +0.08 | -0.70 | 1.12 | 23.2 | +0.07 | 7.7 | +0.06 | +0.01 |
| Half at 2R, rest trails Supertrend | 44,401 | 33.7 | +0.01 | -0.81 | 1.02 | 21.0 | +0.01 | 4.4 | +0.05 | -0.04 |

## Best exit (Stop only, 60 days) by year

| year | trades | win % | avg R | median R | profit factor | avg days | R per 20 days | wins 3R plus % | random avg R | edge R |
|---|---|---|---|---|---|---|---|---|---|---|
| 2022 | 2,222 | 19.5 | -0.44 | -1.03 | 0.48 | 24.5 | -0.36 | 4.2 | -0.18 | -0.26 |
| 2023 | 9,472 | 29.4 | +0.18 | -1.04 | 1.24 | 29.1 | +0.13 | 13.8 | +0.17 | +0.01 |
| 2024 | 13,189 | 29.0 | +0.28 | -1.04 | 1.36 | 28.5 | +0.20 | 15.3 | +0.20 | +0.08 |
| 2025 | 10,090 | 27.0 | +0.11 | -1.03 | 1.14 | 28.4 | +0.08 | 12.4 | +0.16 | -0.05 |
| 2026 | 9,428 | 27.6 | +0.03 | -1.03 | 1.04 | 25.5 | +0.03 | 9.8 | +0.09 | -0.05 |

## Best exit by setup

| setup | trades | win % | avg R | median R | profit factor | avg days | R per 20 days | wins 3R plus % |
|---|---|---|---|---|---|---|---|---|
| breakout_recent | 3,057 | 25.0 | +0.05 | -1.04 | 1.07 | 25.8 | +0.04 | 11.0 |
| breakout_unconfirmed | 2,389 | 25.4 | -0.02 | -1.04 | 0.97 | 27.5 | -0.02 | 11.0 |
| fresh_flip | 7,114 | 30.0 | +0.19 | -1.03 | 1.26 | 29.0 | +0.13 | 13.5 |
| gap_recent | 1,109 | 30.8 | +0.29 | -1.02 | 1.40 | 30.5 | +0.19 | 12.4 |
| pocket_pivot | 12,027 | 28.6 | +0.18 | -1.03 | 1.23 | 28.3 | +0.12 | 12.9 |
| pullback | 12,312 | 26.8 | +0.11 | -1.04 | 1.14 | 26.9 | +0.08 | 12.5 |
| squeeze_fire | 3,074 | 30.8 | +0.15 | -1.03 | 1.20 | 29.5 | +0.10 | 12.0 |
| vcp | 3,319 | 25.3 | +0.07 | -1.05 | 1.08 | 25.6 | +0.05 | 12.8 |

## Best exit by score

| score | trades | win % | avg R | median R | profit factor | avg days | R per 20 days | wins 3R plus % |
|---|---|---|---|---|---|---|---|---|
| 70-80 | 26,284 | 28.6 | +0.12 | -1.03 | 1.16 | 28.2 | +0.09 | 12.4 |
| 80-90 | 16,070 | 27.1 | +0.15 | -1.03 | 1.19 | 27.2 | +0.11 | 12.9 |
| 90+ | 2,047 | 25.2 | +0.12 | -1.03 | 1.14 | 25.8 | +0.09 | 12.6 |

## Best exit by market regime

| regime | trades | win % | avg R | median R | profit factor | avg days | R per 20 days | wins 3R plus % | random avg R | edge R |
|---|---|---|---|---|---|---|---|---|---|---|
| MIXED | 6,838 | 28.6 | +0.08 | -1.03 | 1.10 | 26.8 | +0.06 | 11.1 | +0.21 | -0.13 |
| RISK-OFF | 911 | 31.5 | +0.05 | -1.03 | 1.06 | 30.2 | +0.03 | 8.3 | +0.49 | -0.44 |
| RISK-ON | 36,652 | 27.6 | +0.15 | -1.03 | 1.19 | 27.8 | +0.10 | 13.0 | +0.12 | +0.02 |

Not financial advice. One study on past data; markets change.
