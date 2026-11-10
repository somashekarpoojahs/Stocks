# Trade journal

Every order Claude prepares, and what happened to it. Results are in **R**: 1R = the planned loss at the
stop, so +2R means it made twice the planned risk. Money amounts are left out on purpose (public repo).
Rules: [`ROUTINE.md`](../ROUTINE.md).

| Date | Ticker | Technical | News | Limit | Stop | Status | Exit | R |
|---|---|---|---|---|---|---|---|---|
| 2026-10-21 | DOCU | A+ (89.7): squeeze firing; RS 95; 8/8 trend rules; at 52-week high, but stretched 4.6 ATR above the 50-day | Expanded Salesforce/Agentforce partnership (14 Oct). Analysts' average target $67.63 is below the price | 81.20 | 74.63 | First order at 79.75 cancelled unfilled after the price rose. Re-entered at 81.20 on Poo's call (a 1% chase). **Filled 21 Oct** (average cost 81.85 incl. fees). Open: stop 74.63 GTC; no target; sell by 2 Dec (earnings 3 Dec). 23 Oct: 84.15, above entry, stop order in place. 26 Oct pre-market: 85.04, stop order still in place. 27 Oct pre-market: 84.40, stop order still in place. 28 Oct pre-market: 82.03, stop order still in place. 29 Oct pre-market: about 81, stop order still in place. 30 Oct pre-market: 81.52, stop order still in place. 2 Nov pre-market: 82.08, stop order still in place. 3 Nov: closed 81.65 on 2 Nov, stop order still in place. 4 Nov: closed 80.36 on 3 Nov, stop order still in place. 5 Nov pre-market: 80.61, stop order still in place. 6 Nov pre-market: 77.96, above the stop, stop order still in place. 9 Nov pre-market: 77.61 (6 Nov close), above the stop, stop order still in place. 10 Nov pre-market: closed 77.75 on 9 Nov, above the stop, stop order still in place | – | – |
| 2026-10-21 | DOCU 20 Nov 85/86 call spread | Same DOCU setup as above; spread expires before the 3 Dec earnings | Same as above | 0.45 debit | Whole debit is the risk | Option trade on Poo's request. Not submitted (Poo chose not to use DOCU) | – | – |
| 2026-10-21 | SPY 20 Nov 785/786 call spread | Market RISK-ON; SPY above rising 50/200-day, 0.9% under its record high, up 0.45% on the day | No single-company event: an index fund has no earnings date | 0.42 debit | Whole debit is the risk | Option trade on Poo's request. Not approved. Instruction removed 22 Oct: a day old, and SPY fell ~1% before the open | – | – |
| 2026-10-22 | NFLX 20 Nov 65/64 put spread | Options rules: bearish. Below its 50- and 100-day averages, RSI 33, MACD below zero. Earnings done (20 Oct), next in January | Beat on profit but cut its advertising and revenue outlook (20 Oct); shares −5.3% on 21 Oct | 0.50 debit | Whole debit is the risk | Option trade (Poo: options only today). Not approved. NFLX rose 3.7% on 22 Oct (65.11 open → 67.44); by 13:00 New York the spread was worth about 0.32, so it would have been about −0.36R on paper. Instruction removed 23 Oct (expired idea) | – | – |
| 2026-10-23 | CSX | Long setup, A+ (89.6): gap up holding, pocket pivot, Supertrend flip up; RS 80; 3.0 ATR above the 50-day; earnings reported 21 Oct, next January | Q3 (21 Oct): record revenue +12%, adjusted EPS +30%, operating margin up 8.8 points; TD Cowen raised its target to $55. No takeover or other red flags. Pre-market 51.74 (+0.1%) | 51.67 | 49.34 | Approved by Poo 23 Oct (12:29 UTC). **Filled 23 Oct at the open at 51.23** (average cost 51.75 incl. fees). Open. 26 Oct pre-market: 52.00, above the stop. 27 Oct pre-market: bid 51.25, above the stop. 28 Oct: closed 52.27 on 27 Oct, above the stop. 29 Oct pre-market: 52.77, above the stop. 30 Oct pre-market: 52.92, above the stop. 2 Nov pre-market: 51.78, above the stop. 3 Nov pre-market: 51.82, above the stop. 4 Nov pre-market: 51.30, above the stop. 5 Nov pre-market: 52.23, above the stop. 6 Nov: closed 50.83 on 5 Nov, above the stop. **9 Nov: closed 49.12 on 6 Nov, below the 49.34 stop**; pre-market 49.15 (bid 49.03). No stop order exists, so a SELL LIMIT 49.03 DAY instruction was prepared for approval. Approved. **Sold 9 Nov at the open at 49.40.** Closed | 49.40 | −0.97 |
| 2026-10-26 | R (Ryder) | Long setup, A+ (86.8): base breakout, squeeze firing, gap up holding, pocket pivot, Supertrend flip up; RS 81; 3.8 ATR above the 50-day; earnings reported 22 Oct, next ~February. Also on the trend-restart list | Q3 (22 Oct): comparable EPS +21%, revenue +8%; full-year EPS guidance raised. No downgrade, offering, lawsuit, CEO exit or takeover found. Pre-market bid/ask 270.90/275.00 (no trades yet, ≤ +1.5%) | 270.90 | 257.34 | Instruction prepared 26 Oct (DAY limit). **Not approved** (no fill; instruction expired) | – | – |
| 2026-10-27 | WSFS | Long setup, A+ (88.4): squeeze firing, pocket pivot, Supertrend flip up; RS 80; 1.1 ATR above the 50-day; earnings reported 22 Oct, next January. Also on the trend-restart list | Q3 (22 Oct): EPS 1.75, +28% year on year, beat; wealth and trust fees +30%; big buybacks continue. Watch: problem loans and deposit outflows rose. No downgrade, offering, lawsuit, CEO exit or takeover found. Pre-market 79.78 (+0.3%) | 79.50 | 76.69 | Instruction prepared 27 Oct (DAY limit). Approved. **Filled 27 Oct at 79.19** (average cost 79.98 incl. fees). Open. 28 Oct: closed 78.85 on 27 Oct, above the stop. 29 Oct: closed 78.44 on 28 Oct, above the stop. 30 Oct pre-market: 79.32, above the stop. 2 Nov: closed 78.47 on 30 Oct, above the stop (about 0.6R of room left). 3 Nov: closed 80.52 on 2 Nov, above the stop. 4 Nov: closed 79.90 on 3 Nov, above the stop. 5 Nov pre-market: 81.08, above the stop. 6 Nov: closed 78.93 on 5 Nov, above the stop (about 0.7R of room). 9 Nov: closed 78.94 on 6 Nov, above the stop. 10 Nov: closed 79.89 on 9 Nov, above the stop. ⚠ Still no GTC stop order in IBKR: place sell-stop 76.69 GTC. Exit: hold up to 60 trading days with the first stop; sell before earnings | – | – |
| 2026-11-10 | CPAY | Long setup, A+ (92.5): base breakout, squeeze firing, pocket pivot, hammer candle; RS 89; 3.6 ATR above the 50-day; earnings reported 5 Nov, next 3 Feb | Q3 (5 Nov): beat on revenue ($1.38B, organic +11%) and adjusted EPS ($7.54 vs $7.20); full-year guidance raised to ~$28 EPS; shares +8–10% to a 52-week high. No new downgrade, offering, CEO exit or takeover found (FTC fuel-card injunction is old news). Pre-market bid 460.26 (+0.5%) | 457.97 | 428.70 | Instruction prepared 10 Nov (DAY limit). Exit: hold up to 60 trading days with the first stop; sell before 3 Feb earnings | – | – |

2026-10-28: no new order. 3 positions already open (DOCU, CSX, WSFS), the maximum.

2026-10-29: no new order. 3 positions still open (DOCU, CSX, WSFS), the maximum.

2026-10-30: no new order. 3 positions still open (DOCU, CSX, WSFS), the maximum.

2026-11-02: no new order. 3 positions still open (DOCU, CSX, WSFS), the maximum.

2026-11-03: no new order. 3 positions still open (DOCU, CSX, WSFS), the maximum.

2026-11-04: no new order. 3 positions still open (DOCU, CSX, WSFS), the maximum.

2026-11-05: no new order. 3 positions still open (DOCU, CSX, WSFS), the maximum. (The scan also lacked 4 Nov data; a re-run was started.)

2026-11-06: no new order. 3 positions still open (DOCU, CSX, WSFS), the maximum. Scan for 5 Nov arrived 12:18 UTC; market RISK-ON.

2026-11-09: no new order. 3 positions still open (DOCU, CSX, WSFS), the maximum. CSX closed below its stop on 6 Nov with no stop order: SELL instruction prepared. Market MIXED.

2026-11-10: CSX was sold on 9 Nov (−0.97R), leaving 2 open (DOCU, WSFS). Market RISK-ON. New BUY instruction prepared: CPAY.

## Running stats

| Trades closed | Win rate | Average R | Total R |
|---|---|---|---|
| 1 | 0% (0 of 1) | −0.97 | −0.97 |
