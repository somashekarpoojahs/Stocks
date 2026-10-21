# Daily pre-market routine

Every US trading day, before the open, Claude prepares **at most one** stock order and Poo approves or
skips it in IBKR. Nothing is ever placed without that approval: the IBKR connection is in
review-and-approve mode, and Claude can only create order *instructions*.

| Time (UTC) | Irish summer / winter | What happens |
|---|---|---|
| 21:40 (evening before) | 22:40 / 21:40 | GitHub runs the scan of ~1,500 stocks on the day's complete bars → `scans/latest.md` (07:00 UTC re-run as a backup) |
| 12:15 | 13:15 / 12:15 | Claude checks the picks (chart + news + live price), prepares the order, updates `trades/journal.md`, sends a phone notification |
| 13:30 | 14:30 / 13:30* | US market opens (*14:30 UTC after US clocks change on 1 Nov) |

## Rules for choosing the order

1. **Market first.** Read `scans/latest.md`. It must be from the previous US trading day. If the market
   is **RISK-OFF**, no new buys.
2. **Technical shortlist.** Two sources:
   - Long setups graded A+ or A.
   - **Trend restarts** with RS 50 or more (`scans/latest_restarts.csv`): the Supertrend (7, 3) just flipped
     back up after a pullback in an uptrend, the pattern from Poo's QQQ and MU charts. In the 5-year study,
     restarts with RS under 50 did worst.

   Then, for both:
   - Skip anything with earnings in the next 15 trading days. A trade is held for up to 60 days but is always sold before earnings.
   - Skip anything stretched more than 5 ATR above its 50-day average ("Ext ATR").
   - Skip anything pinned near a takeover price.
   - Prefer gap up holding, pocket pivot, Supertrend flip up, and squeeze firing. These did best in the 4.5-year exit study.
3. **News check** on the top ~5, covering the last 7 days.
   - Need a real positive catalyst: results or guidance raised, a partnership or contract, an upgrade.
   - No red flags: downgrade, lawsuit, share offering, guidance cut, CEO exit, takeover.
   - Pick the one where **chart and news agree** best.
4. **Live check in IBKR** (pre-market quote).
   - Skip if the price is below the stop.
   - Skip if it is more than 3% above yesterday's close. Don't chase.
5. **The order:**
   - BUY, LIMIT at or just below yesterday's close (never more than 0.5% above it), DAY.
   - **Size:** the loss at the stop, *including both commissions*, is at most 2% of the account's net liquidation value. Commissions use IBKR Pro Fixed: max($1, $0.005/share), capped at 1% of the order. Fractional shares go to 2 decimals.
   - At most 3 open positions. No new order if 3 are already open.
6. **Stop:** the scanner's stop. For a trend restart, it is the Supertrend (7, 3) line shown in the report
   (at most 15% below). The IBKR connection can't create stop orders, so Poo attaches it when
   submitting: **Attach order → Stop loss**, GTC. If that isn't offered for a fractional order, Poo places a
   separate GTC sell-stop right after the fill.
7. **Exit plan** (the same for trend restarts):
   - No fixed target: hold up to 60 trading days while the price stays above the stop. Don't trail the stop
     up the Supertrend line: in the study that earned less than leaving the first stop in place.
   - Sell before earnings: Claude prepares a SELL instruction 1–2 days ahead.
   - Also prepare a SELL if the stop is broken but the stop order is missing.
8. **Journal:** one row per prepared order in `trades/journal.md`, updated each day: approved?, filled,
   open, stopped, sold. Results go in **R**, where 1R = the planned risk. No money amounts, because this repo is public.
9. **"No trade today" is a valid result.**

## Why these rules

The exit study (`research/exit_study_2026-10-21.md`) covered 4.5 years and 44,401 trades.

- Holding with only the stop beat fixed profit targets.
- The scanner's picks did **no better than random stocks** bought on the same days.

The trend-restart study (`research/restart_study_2026-10-21.md`) covered 5,777 restarts from
September 2022 to October 2026.

- It caught QQQ and MU on 8 April 2026, the start of their big moves.
- On average, though, restarts did about as well as random stocks bought the same days: +0.22R vs +0.21R
  with the stop held for up to 60 days. With the chart's own exit (sell when the Supertrend line breaks),
  they made +0.10R vs +0.13R, and 60% of trades lost.
- Plain Supertrend (7, 3) buy arrows (22,782 of them) also matched random stocks: +0.06R vs +0.08R.

So these rules don't promise profit. They keep each loss small and record every result, so the real
numbers show whether this works before any size increase.
