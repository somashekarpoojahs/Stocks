# Technical options spread system

> Notes from 20 Oct 2026, kept for reference. For daily stock picks use the Smart Scanner (see the main README). Code for this system: `extras/signals.py` and `extras/tenx.py`.

## Setup (chosen 20 Oct 2026)
- Strategy: technical signals traded with defined-risk vertical (debit) spreads
- Universe: large-cap US stocks (AAPL, MSFT, NVDA, AMD, BAC, INTC, PFE, KO, XOM, NFLX)
- Orders: prepared as IBKR order instructions; you review and submit each one in IBKR yourself
- Sizing: 1 contract per trade. On a small account the 2% risk rule can't be met with spreads (the cheapest risked ~$35-55), so the choice was to trade small live anyway, approving each trade.

## Signal rules (daily bars)
- BULLISH: close > SMA50 > SMA100, RSI(14) 45-70, MACD(12,26,9) histogram > 0 or rising
- BEARISH: close < SMA50 < SMA100, RSI(14) 30-55, MACD histogram < 0 or falling
- Otherwise: no trade
- Skip any name with earnings before the spread's expiry, unless taking earnings risk on purpose
- ATR(14) guides strike width and expected move

## Trade construction
- Bullish: buy call at/near the money, sell call $1 higher (or next strike)
- Bearish: buy put at/near the money, sell put $1 lower
- Expiry: 2-4 weeks out; enter with a LIMIT order at or near the mid price
- Max loss = debit paid x 100; max gain = (width - debit) x 100

## Scan log
### 20 Oct 2026 (intraday)
| Ticker | Signal | Earnings | Status |
|---|---|---|---|
| KO | Bullish (RSI 67.7, MACD hist fading) | 27 Oct, before open | Candidate only if earnings risk accepted |
| XOM | Bullish (RSI 66.4, MACD hist fading) | 30 Oct, before open | Skipped: earnings + Iran/oil headline risk |
| INTC | Bearish (down 25% in 20 days, RSI 36) | 29 Oct, after close | Skipped: earnings, already extended |
| NFLX | Bearish | 20 Oct, after close | Skipped: earnings tonight |
| AAPL, MSFT, NVDA, AMD, BAC, PFE | No signal | - | - |

KO Nov 6 call spreads (delayed quotes, spot 92.89): 93/94 ~0.46 debit ($46 risk, $54 max gain, breakeven 93.46); 94/95 ~0.37 debit ($37 risk, $63 max gain, breakeven 94.37).

## 10x earnings-option scan (20 Oct 2026, ~19:00 Irish time)
Goal: single options that could return ~10x. Method: this week's earnings reporters where options are liquid; move needed by Fri 23 Oct expiry for the option to be worth 10x its ask, compared with the options-implied move and the stock's historical average earnings move (EarningsWatcher). "x avg" = needed move / average move (lower = less unlikely). Quotes delayed ~15 min.

| Rank | Option (exp 23 Oct) | Cost | 10x needs | Implied / avg move | x avg | Liquidity | Technical |
|---|---|---|---|---|---|---|---|
| 1 | BE 185 put | $131 | -23.0% | 12.4% / 16.5% | 1.39 | OK | Bearish (aligned) |
| 2 | TSLA 330 put | $82 | -14.1% | 7.3% / 9.6% | 1.47 | Very good | Neutral |
| 3 | BE 175 put | $66 (mid ~$57) | -24.5% | 12.4% / 16.5% | 1.49 | Wide spread | Bearish (aligned) |
| 4 | META 600 put | $172 | -15.7% | 7.1% / 10.4% | 1.51 | Good | Neutral |
| 5 | TSLA 420 call | $128 | +15.6% | 7.3% / 9.6% | 1.62 | Very good | Neutral |
| 6 | NFLX 60 put | $41 | -19.3% | 9.4% / 10.2% | 1.89 | Very good | Bearish (aligned) |
| 7 | WDC 300 put | $98 | -20.2% | 10.3% / 9.4% | 2.15 | Wide spread | Bearish (aligned) |

Earnings: NFLX Tue 20 Oct after close; META, TSLA Wed 21 Oct after close; SPOT Thu 22 Oct before open; BE, WDC Thu 22 Oct after close.
Excluded: SPOT calls (too expensive, very thin open interest), HUMA (PDUFA 22 Oct, but ~$0.40 stock with almost no options volume), META calls/puts above ~$170 (too large for the account).
Every option here needs at least ~1.4x the stock's usual earnings move; market-implied chance of finishing in the money is ~4-12%, and of 10x lower still.
Technical scan of catalyst names (signals.py): BE bearish, WDC bearish, SPOT bullish, META and TSLA no signal.

## Notes
- IBKR option quotes were delayed ~15 min (no live options data subscription); stock quotes were real-time.
- US option trades need options/spread trading permissions in IBKR, and USD in the account (convert first if it holds EUR).
- Scanner code: `extras/signals.py` (reads a JSON of daily closes plus the last 15 highs/lows per ticker).
