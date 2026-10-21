"""Every tunable setting lives here, so rules can be changed without touching code."""
from dataclasses import dataclass

FEE_PLANS = {                     # (minimum per order, per share, max % of trade value)
    "ibkr-fixed": (1.00, 0.005, 0.01),
    "ibkr-tiered": (0.35, 0.0035, 0.01),
    "none": (0.0, 0.0, 0.0),
}


@dataclass
class Config:
    # ---- universe filters (applied to the latest bar) ----
    min_price: float = 5.0                 # skip penny stocks
    min_dollar_volume: float = 10_000_000  # 50-day average daily $ traded
    min_bars: int = 60                     # need at least this much history

    # ---- benchmark used for regime + relative strength ----
    benchmark: str = "SPY"

    # ---- setup detection ----
    rvol_breakout: float = 1.5     # breakout volume vs 50-day average
    base_lookback: int = 60        # bars that define a base / pivot high
    base_min_len: int = 25
    base_max_depth: float = 0.35   # base can't be deeper than 35%
    gap_min_pct: float = 0.03      # 3%+ gap up
    supertrend_period: int = 10
    supertrend_mult: float = 3.0
    fresh_flip_bars: int = 10      # Supertrend flip counts as "fresh" for 10 bars

    # ---- trade plan / position sizing ----
    account_size: float = 1000.0        # in account currency (set yours: --account or SCANNER_ACCOUNT)
    account_ccy_per_usd: float = 1.0    # e.g. 0.89 when the account is in EUR
    risk_per_trade: float = 0.02        # 2% of the account lost if the stop hits
    max_stop_pct: float = 0.10          # never risk more than 10% below entry
    allow_fractional: bool = True       # IBKR offers fractional US shares

    # ---- broker fees per order, USD (default: IBKR Pro Fixed for US stocks) ----
    # fee = max(fee_min_usd, fee_per_share_usd * shares), capped at fee_max_pct of trade value.
    # Exchange/regulatory fees are not included. On a small account these matter:
    # ~1% of the position per side, so they come out of the risk budget.
    fee_min_usd: float = 1.00
    fee_per_share_usd: float = 0.005
    fee_max_pct: float = 0.01

    # ---- backtest ----
    backtest_cost_pct: float = 0.001    # slippage per side (0.1%) on top of the signal's R

    # ---- output ----
    top_n: int = 30
    min_long_score: float = 60.0
    min_short_score: float = 60.0
