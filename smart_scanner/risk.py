"""Turns a signal into a concrete plan: entry, stop, targets and position size."""
import math

import numpy as np


def _num(row, key):
    v = row.get(key, np.nan)
    try:
        v = float(v)
    except (TypeError, ValueError):
        return np.nan
    return v


def order_fee(shares: float, price: float, cfg) -> float:
    """Commission for one order (IBKR-style minimum, per-share rate and % cap)."""
    if shares <= 0 or (cfg.fee_min_usd <= 0 and cfg.fee_per_share_usd <= 0):
        return 0.0
    fee = max(cfg.fee_min_usd, cfg.fee_per_share_usd * shares)
    if cfg.fee_max_pct > 0:
        fee = min(fee, cfg.fee_max_pct * shares * price)
    return fee


def position_size(entry: float, stop: float, risk_usd: float, cash_usd: float, cfg) -> float:
    """Largest size whose loss at the stop *including both commissions* stays within
    the risk budget, and whose cost fits in the cash. Loss and cost both grow with
    size, so a bisection finds the edge."""
    r = abs(entry - stop)
    if r <= 0 or risk_usd <= 0:
        return 0.0
    loss = lambda s: s * r + order_fee(s, entry, cfg) + order_fee(s, stop, cfg)
    cost = lambda s: s * entry + order_fee(s, entry, cfg)
    ok = lambda s: loss(s) <= risk_usd + 1e-12 and cost(s) <= cash_usd + 1e-12
    lo, hi = 0.0, min(risk_usd / r, cash_usd / entry)
    if ok(hi):
        lo = hi
    else:
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if ok(mid) else (lo, mid)
    return math.floor(lo) if not cfg.allow_fractional else lo


def trade_plan(row, cfg, side: str = "long") -> dict:
    entry = float(row["close"])
    a = float(row["atr"]) if not np.isnan(row["atr"]) else entry * 0.03
    if side == "long":
        stops = [entry - 2 * a]
        if row.get("st_dir", 0) == 1 and not np.isnan(row["st_line"]) and row["st_line"] < entry - 0.5 * a:
            stops.append(float(row["st_line"]))
        level = _num(row, "breakout_level")
        if bool(row.get("breakout_recent", False)) and not np.isnan(level):
            stops.append(level - 0.5 * a)                          # just under the level it broke
        ceiling = entry - a                                        # at least 1 ATR of room...
        low = _num(row, "low")
        if not np.isnan(low):
            ceiling = min(ceiling, low - 0.1 * a)                  # ...and never inside today's range
        stop = min(max(stops), ceiling)
        wide = (entry - stop) / entry > cfg.max_stop_pct
        if wide:
            stop = entry * (1 - cfg.max_stop_pct)
        r = entry - stop
        t1, t2 = entry + 2 * r, entry + 3 * r
    else:
        stops = [entry + 2 * a]
        if row.get("st_dir", 0) == -1 and not np.isnan(row["st_line"]) and row["st_line"] > entry + 0.5 * a:
            stops.append(float(row["st_line"]))
        floor = entry + a
        high = _num(row, "high")
        if not np.isnan(high):
            floor = max(floor, high + 0.1 * a)
        stop = max(min(stops), floor)
        wide = (stop - entry) / entry > cfg.max_stop_pct
        if wide:
            stop = entry * (1 + cfg.max_stop_pct)
        r = stop - entry
        t1, t2 = entry - 2 * r, entry - 3 * r
    return _sized(entry, stop, r, t1, t2, wide, cfg)


def restart_plan(row, cfg) -> dict:
    """Plan for a trend restart: the stop is the Supertrend (7, 3) line under the price
    (where the chart's trend turns back down), at most `restart_max_stop_pct` below
    and never inside today's range. Without an up-trending line (e.g. the random
    stocks in the study) it falls back to 3 ATR, about where a fresh line sits."""
    entry = float(row["close"])
    a = float(row["atr"]) if not np.isnan(row["atr"]) else entry * 0.03
    line = _num(row, "st7_line")
    up = row.get("st7_dir", 0) == 1 and not np.isnan(line) and line < entry
    stop = line if up else entry - 3 * a
    stop = min(stop, entry - a)                                  # at least 1 ATR of room
    low = _num(row, "low")
    if not np.isnan(low):
        stop = min(stop, low - 0.1 * a)                          # never inside today's range
    wide = (entry - stop) / entry > cfg.restart_max_stop_pct
    if wide:
        stop = entry * (1 - cfg.restart_max_stop_pct)
    r = entry - stop
    return _sized(entry, stop, r, entry + 2 * r, entry + 3 * r, wide, cfg)


def _sized(entry, stop, r, t1, t2, wide, cfg) -> dict:
    budget = cfg.account_size * cfg.risk_per_trade / cfg.account_ccy_per_usd
    cash_usd = cfg.account_size / cfg.account_ccy_per_usd
    shares = position_size(entry, stop, budget, cash_usd, cfg)
    if cfg.allow_fractional:
        shares = math.floor(shares * 1000) / 1000          # keep 3 decimals, rounding down
    fees = order_fee(shares, entry, cfg) + order_fee(shares, stop, cfg)
    loss_at_stop = shares * r + fees
    gain_at_2r = shares * 2 * r - order_fee(shares, entry, cfg) - order_fee(shares, t1, cfg)
    net_rr = gain_at_2r / loss_at_stop if loss_at_stop > 0 else np.nan
    return {
        "entry": round(entry, 2), "stop": round(stop, 2), "stop_pct": round(100 * r / entry, 1),
        "target_2r": round(t1, 2), "target_3r": round(t2, 2), "stop_capped": bool(wide),
        "shares": shares, "position_usd": round(shares * entry, 2),
        "fees_usd": round(fees, 2),                         # round trip, exit at the stop
        "risk_usd": round(loss_at_stop, 2),                 # total loss if the stop hits
        "risk_budget_usd": round(budget, 2),
        "net_rr": round(net_rr, 2),                         # what the 2R target really pays after fees
    }
