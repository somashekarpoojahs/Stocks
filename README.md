# Stocks · Smart Scanner

A whole-market swing-trading scanner for US stocks, plus notes and tools from building it.

Every weekday morning, before the US market opens, a GitHub Action scores about 1,500 stocks on ~30 indicators plus chart and
candlestick patterns. It checks the market's mood and saves a report to [`scans/latest.md`](scans/latest.md)
(it opens nicely in the GitHub phone app). The report has:

- ranked buy candidates,
- a watchlist of stocks just under a breakout,
- put/short candidates,
- a complete trade plan for each: entry, stop, targets, share count, commissions and real reward-to-risk.

It finds candidates. It never places trades. Not financial advice.

| Folder | What's in it |
|---|---|
| `smart_scanner/` | The scanner (Python package) |
| `tests/` | 43 automated tests |
| `scans/` | Daily reports, written by the GitHub Action (`latest.md`, plus one folder per day) |
| `research/` | Exit studies: which way of selling works best, on years of data |
| `trades/` | Trade journal: every order Claude prepares and its result (in R) |
| `ROUTINE.md` | The daily pre-market routine: how the one order a day is chosen |
| `examples/` | A sample report (13 stocks, 20 Oct 2026) |
| `docs/` | Notes: the options spread system and the first trend-start scanner |
| `extras/` | Earlier one-off tools (options signals, 10x earnings-option screen, trend-start scanner) |

## How it decides (four stages)

**1. Universe and data.** By default the S&P 1500 (or the S&P 500/400/600, Nasdaq-100 or your own
list), using 2 years of daily bars from Yahoo. Stocks under $5 or trading under $10M a day are skipped.

**2. Market regime.** Five checks:

- SPY above its 50-day average.
- SPY above its 200-day average.
- 200-day average rising.
- Over half of stocks above their 50-day.
- More new 52-week highs than lows.

The result is **RISK-ON**, **MIXED** or **RISK-OFF**, and every score is scaled by it. Most
breakouts fail in a RISK-OFF market.

**3. Score 0–100 per stock**, built from five parts:

| Part | Weight | Built from |
|---|---|---|
| Trend | 30% | Minervini trend template (8 rules), Weinstein stage, Supertrend (10, 3), ADX / ±DI |
| Momentum | 20% | RS rating 1–99 (IBD-style, weighted 3/6/9/12-month return), RSI (14), MACD (12, 26, 9) histogram |
| Volume | 15% | Up/down volume ratio (50 days), Chaikin Money Flow (20), OBV vs its 21-day EMA |
| Setup | 20% | The trigger, from the table below, plus a confirming candle |
| Risk | 15% | How stretched the price is above its 50-day average (in ATRs), with a penalty above RSI 80 |

Grades:

- **A+** needs a score of 80+ *and* confluence: RS 80+, at least 7 of the 8 trend rules, and a primary setup.
- **A** needs a score of 70+.
- **B** needs a score of 60+.

One lucky indicator can't produce an A+.

| Setup | Meaning | Strength |
|---|---|---|
| Base breakout | First close above the high of a ≤35%-deep base, on ≥1.5× average volume | 1.00 · primary |
| VCP | Three pullbacks, each shallower, volume drying up, near highs | 0.90 · primary |
| Squeeze firing | Bollinger Bands were inside Keltner Channels and now break out upward | 0.80 · primary |
| Gap up holding | Gap of ≥3% on ≥2× volume that closes in the upper half and holds above the 20-day | 0.80 · primary |
| Pullback to 21-EMA | Uptrend dips to a rising 21-day EMA, RSI 40–60, bullish candle | 0.75 · primary |
| Pocket pivot | Up-day volume beats every down-day of the last 10 days | 0.60 |
| Breakout, volume unconfirmed | Closed above the pivot without the volume (yet) | 0.55 |
| Supertrend flip up | Supertrend turned up within the last 10 bars | 0.50 |

- **Short/put side:** breakdown below a base on volume, failed breakout, Supertrend flip down.
- **Candles** (confirmation only): engulfing, hammer, shooting star, morning/evening star, three white soldiers, doji, inside bar, NR7, marubozu.

**4. Trade plan.**

- **Stop:** the tightest sensible of 2×ATR, the Supertrend line, or just under the breakout level. It is never placed inside today's price range and is capped at 10%.
- **Targets:** 2R and 3R.
- **Size:** chosen so that the loss at the stop, *including both commissions*, is your risk per trade (2% by default). Fractional shares are used.

Each plan is sized on its own. Don't hold more than 2–3 positions at once.

## Daily scan on GitHub (already set up)

The workflow `.github/workflows/scan.yml` runs Monday–Friday at 11:30 UTC (12:30 Irish time in summer, 11:30
in winter), before the US open. It scans the previous day's complete bars, so the picks are ready before
the bell. GitHub sometimes starts scheduled runs a few minutes late. You can also run it any time:
**Actions → daily-scan → Run workflow**. Each run saves:

- `scans/latest.md` and `scans/latest.html`,
- `scans/latest_longs.csv` / `_watch` / `_shorts`,
- a dated folder `scans/YYYY-MM-DD/`.

**Set your own numbers once.** Go to **Settings → Secrets and variables → Actions → Variables → New
repository variable**:

| Variable | Example | Default if unset |
|---|---|---|
| `ACCOUNT_SIZE` | `500` | `1000` |
| `CCY_PER_USD` | `0.89` if you size in EUR | `1.0` |
| `RISK` | `0.02` | `0.02` |
| `FEES` | `ibkr-fixed`, `ibkr-tiered` or `none` | `ibkr-fixed` |
| `UNIVERSE` | `sp500` | `sp1500` |

**Privacy:** this repo is public. Reports show position sizes, which reveal roughly how big your
account is once `ACCOUNT_SIZE` is set. To keep that private, go to **Settings → General → Danger Zone →
Change visibility**. Private repos get 2,000 free Actions minutes a month; a daily scan uses about 10.

Prefer GitLab? `.gitlab-ci.yml` does the same there (artifacts instead of commits).

## Run it on a laptop

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q                                       # 43 tests, ~30 s
python -m smart_scanner scan --universe sp1500 --account 500 --with-backtest
```

Then open `reports/scan_YYYY-MM-DD.html` (or the `.md`).

- Run it **between the US close (21:00 Irish time) and the next open (14:30)**. During the session it would
  see an unfinished day, and the report says so.
- The first run of the day downloads ~1,500 tickers (5–10 minutes). Later runs that day use the cache; add `--refresh` to re-download.
- Instead of flags, you can set `SCANNER_ACCOUNT`, `SCANNER_CCY_PER_USD`, `SCANNER_RISK`, `SCANNER_FEES` and `SCANNER_UNIVERSE` in your shell.

| Option | Default | Meaning |
|---|---|---|
| `--universe` | `sp1500` | `sp500`, `sp400`, `sp600`, `nasdaq100`, `file:my_list.txt`, or `AAPL,MSFT,NVDA` |
| `--account` | `1000` | Account size, in its own currency |
| `--ccy-per-usd` | `1.0` | Use `0.89` if you size in EUR |
| `--risk` | `0.02` | Fraction of the account you may lose per trade |
| `--fees` | `ibkr-fixed` | `ibkr-tiered` or `none`. Used for sizing and net reward-to-risk |
| `--with-backtest` | off | Add a backtest of these rules to the report |
| `--source` | `yahoo` | `json:FILE` (e.g. IBKR price history, used as-is) or `csvdir:FOLDER` |

## Daily routine with Claude

1. Read the report's **market banner and "Check before acting" box** first.
2. Ask Claude to *"check tonight's scan"*. It reads `scans/latest.md` straight from this repo.
3. For the top 2–3 names, Claude checks IBKR:
   - live quote,
   - earnings date,
   - news,
   - option chain (if you want a spread).

   It then recomputes the plan at live prices and your real balance.
4. Claude prepares the order and its stop as an **IBKR order instruction**. You review and submit it in
   IBKR yourself. Nothing is ever placed without you.
5. For watchlist names Claude can set **IBKR price alerts** at the pivot.

## Rules that protect a small account

- Lose at most 2% per trade, commissions included. Enter the stop together with the order.
- Skip a trade if earnings are within 7 days (⚠ in the report).
- In RISK-OFF, take no new longs except an A+ at half size.
- Hold at most 2–3 open positions.
- **Commissions matter.** IBKR Pro Fixed charges max($1, $0.005/share), capped at 1% of the order. On
  accounts under ~$1,000 that takes roughly 10–25% of each trade's risk budget. The **Net R:R** column
  shows what a "2R" target really pays after fees. Tight-stop trades suffer most, so favour fewer setups
  with wider targets.

## Backtest: what it can and can't tell you

```bash
python -m smart_scanner backtest --universe sp500 --threshold 70
```

How it works:

- **Walk-forward:** each signal uses only data up to its day.
- **Entry:** the next open.
- **Exit:** stop, 2R or 20 days. If both the stop and the target are hit on the same day, the stop is assumed first.
- **Slippage:** 0.1% per side.

Results are grouped by score, setup and regime, next to a baseline (an average stock over 20 days).

- **Survivorship bias:** it uses *today's* index members, which flatters results. Read it as a check
  of which setups pull their weight, not as a forecast.
- If a setup's `avg_R` stays at or below 0 over hundreds of trades, lower its weight in `smart_scanner/scoring.py`.

**Exit study.** `python -m smart_scanner study --period 5y` (or **Actions → exit-study → Run workflow**)
takes the same entries and compares eight ways of selling:

- fixed 2R or 3R targets,
- holding with only the stop,
- trailing stops (3 ATR, Supertrend),
- selling on a close below the 21-EMA or the 50-day,
- selling half at 2R.

Each is set against random stocks bought on the same days, so you can see whether the stock picking
itself adds anything. Results go to `research/`.

## Honest limits

- **So far the picks haven't beaten random stocks.** The exit study
  ([`research/exit_study_2026-10-21.md`](research/exit_study_2026-10-21.md)) covered March 2022 to October 2026:
  44,401 trades on 1,496 stocks.
  - Under every exit rule, the scanner's picks did about as well as random stocks bought on the same days.
    The gap was between −0.04R and +0.01R per trade.
  - The best exit was holding with only the stop for up to 60 days. Picks made +0.13R per trade; random stocks made +0.14R.
  - Higher scores did no better than lower ones.
  - Picks beat random stocks in 2 of 5 years.

  The gains came from the market rising, not from the picking. Use the scanner to find and study setups,
  not as a proven edge.
- Daily bars only: no intraday timing.
- Yahoo data is free and occasionally late or wrong. IBKR's quote is the reference before ordering.
- No fundamentals or news. A perfect chart can meet bad news the next morning. That is why step 3
  checks earnings and news.
- No scanner can pick the 10x/100x winners in advance. Big winners usually show high RS and break out
  of a base *before* most of their move, and that is what this hunts for. Most breakouts still fail,
  and the stop is what keeps those losses small.

## Code layout

```
smart_scanner/
  config.py      every tunable number (filters, setups, sizing, fees)
  indicators.py  SMA/EMA, Wilder RSI/ATR/ADX, MACD, Supertrend, Bollinger, Keltner, OBV, CMF, RVOL, RS
  patterns.py    candles, base breakout, VCP, pocket pivot, gaps, pullbacks, squeeze, trend template, stages
  features.py    builds all of the above per stock (strictly causal: no look-ahead, tested)
  scoring.py     RS rating, breadth, regime, the five score parts, grades
  risk.py        stops, targets, commission-aware position sizing
  pipeline.py    runs everything and ranks longs / watchlist / shorts, plus data-quality warnings
  backtest.py    walk-forward test of the same rules
  report.py      HTML, Markdown and CSV reports
  data.py        Yahoo (cached, retried), JSON (incl. IBKR price history as-is), CSV folders
  universe.py    S&P 500 (GitHub datasets), S&P 400/600 and Nasdaq-100 (Wikipedia)
  cli.py         python -m smart_scanner scan | backtest
```

Commission figures are from IBKR's
[commissions page](https://interactivebrokers.ie/en/index.php?f=49807). Check them against your own
plan; exchange and regulatory fees are not included.
