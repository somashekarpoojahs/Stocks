import numpy as np
import pandas as pd
import pytest

from smart_scanner.backtest import backtest
from smart_scanner.config import Config
from smart_scanner.features import compute_features
from smart_scanner.pipeline import run_scan
from smart_scanner.report import build_html
from smart_scanner.risk import trade_plan
from conftest import random_walk


def test_no_look_ahead(cfg):
    """A feature value on day k must not change when later bars are added."""
    df = random_walk(320, seed=5, drift=0.001)
    full = compute_features(df, cfg)
    for k in (150, 230, 300):
        part = compute_features(df.iloc[:k], cfg)
        a, b = part.iloc[-1], full.iloc[k - 1]
        for col in part.columns:
            x, y = a[col], b[col]
            if isinstance(x, (float, np.floating)) and np.isnan(x):
                assert np.isnan(y), col
            else:
                assert x == pytest.approx(y, rel=1e-9, abs=1e-9), col


def test_scan_ranks_breakout_first_and_finds_breakdown(universe, cfg):
    res = run_scan(universe, cfg)
    assert not res.longs.empty and res.longs.iloc[0]["ticker"] == "BRK"
    top = res.longs.iloc[0]
    assert "Base breakout" in top["setups"] and top["score"] >= 70
    assert top["stop"] < top["close"] < top["target_2r"]
    assert "DWN" in set(res.shorts["ticker"])
    assert res.regime_label.iloc[-1] in {"RISK-ON", "MIXED", "RISK-OFF"}
    assert res.feats["BRK"]["rs_rating"].iloc[-1] >= 80      # a market leader (A+ needs 80+)


def test_top_grade_needs_confluence(universe, cfg):
    res = run_scan(universe, cfg)
    primary = ("Base breakout", "VCP", "Squeeze firing", "Gap up", "Pullback")
    for _, r in res.longs[res.longs["grade"] == "A+"].iterrows():
        assert any(p in r["setups"] for p in primary), r["ticker"]
        assert r["rs_rating"] >= 80 and r["trend_template"] >= 7
    assert res.longs.iloc[0]["grade"] == "A+" and res.longs.iloc[0]["ticker"] == "BRK"
    assert all("bearish" not in s for s in res.longs["setups"])


def test_trade_plan_sizing():
    cfg = Config(account_size=500, account_ccy_per_usd=0.89, risk_per_trade=0.02,
                 fee_min_usd=0, fee_per_share_usd=0, fee_max_pct=0)
    row = pd.Series({"close": 100.0, "atr": 4.0, "st_dir": 1, "st_line": 93.0,
                     "breakout_recent": False, "pivot": np.nan})
    p = trade_plan(row, cfg, "long")
    assert p["stop"] == 93.0                       # Supertrend line is the tightest sensible stop
    risk_usd = 500 * 0.02 / 0.89
    assert p["shares"] == pytest.approx(risk_usd / 7.0, abs=1e-3)
    assert p["risk_usd"] == pytest.approx(risk_usd, abs=0.01)
    assert p["target_2r"] == 114.0


def test_fees_come_out_of_the_risk_budget():
    """IBKR Pro Fixed: max($1, $0.005/share) capped at 1% of the order's value."""
    from smart_scanner.risk import order_fee
    cfg = Config(account_size=300)                  # small account, 2% risk, IBKR fixed fees
    assert order_fee(2, 13.78, cfg) == pytest.approx(0.01 * 2 * 13.78)    # tiny order: 1% cap
    assert order_fee(500, 50.0, cfg) == pytest.approx(2.50)               # 0.005 x 500
    assert order_fee(100, 50.0, cfg) == pytest.approx(1.00)               # minimum
    row = pd.Series({"close": 100.0, "atr": 4.0, "st_dir": 1, "st_line": 93.0})
    with_fees = trade_plan(row, cfg, "long")
    no_fees = trade_plan(row, Config(account_size=300, fee_min_usd=0, fee_per_share_usd=0, fee_max_pct=0), "long")
    assert with_fees["fees_usd"] > 0 and with_fees["shares"] < no_fees["shares"]
    assert with_fees["risk_usd"] <= 300 * 0.02 + 1e-9                   # loss incl. fees within 2%
    assert no_fees["net_rr"] == pytest.approx(2.0, abs=0.01) and with_fees["net_rr"] < 2.0


def test_trade_plan_caps_wide_stop():
    cfg = Config(max_stop_pct=0.10)
    row = pd.Series({"close": 100.0, "atr": 9.0, "st_dir": 1, "st_line": 70.0,
                     "breakout_recent": False, "pivot": np.nan})
    p = trade_plan(row, cfg, "long")
    assert p["stop"] == 90.0 and p["stop_capped"]


def test_trade_plan_never_exceeds_cash():
    cfg = Config(account_size=300, account_ccy_per_usd=1.0, risk_per_trade=0.5)
    row = pd.Series({"close": 50.0, "atr": 0.5, "st_dir": 1, "st_line": 49.0,
                     "breakout_recent": False, "pivot": np.nan})
    assert trade_plan(row, cfg, "long")["position_usd"] <= 300.0 + 1e-6


def test_backtest_runs(universe, cfg):
    r = backtest(universe, cfg, threshold=60)
    assert {"trades", "win_rate_%", "avg_R"} <= set(r.summary.columns) or r.trades.empty
    if not r.trades.empty:
        stops = r.trades[r.trades["reason"] == "stop"]
        assert (stops["R"] <= -0.99).all()         # a stop loses ~1R (more on gaps)


def test_report_html(universe, cfg):
    html = build_html(run_scan(universe, cfg))
    assert "BRK" in html and "<table" in html and "regime" in html


def test_small_universe_rs_is_anchored_to_benchmark(cfg):
    """In a 6-stock watchlist that all lag a rising market, the 'best' laggard
    must not be rated as a market leader (a pure rank would give it 99)."""
    data = {"SPY": random_walk(300, seed=1, drift=0.0015, sigma=0.008)}
    for i in range(6):
        data[f"L{i}"] = random_walk(300, seed=40 + i, drift=-0.0008 - 0.0002 * i, sigma=0.01)
    res = run_scan(data, cfg)
    last_rs = [f["rs_rating"].iloc[-1] for f in res.feats.values()]
    assert max(last_rs) < 40
    assert any("measured against the S&P 500" in w for w in res.warnings)


def test_rs_is_a_rank_in_a_big_universe():
    from smart_scanner.scoring import rs_rating
    idx = pd.RangeIndex(3)
    feats = {f"S{i}": pd.DataFrame({"rs_raw": [i / 100.0] * 3}, index=idx) for i in range(150)}
    rs = rs_rating(feats, pd.Series([5.0] * 3, index=idx))   # benchmark far ahead: ignored at n=150
    assert rs["S149"].iloc[-1] == 99 and rs["S0"].iloc[-1] <= 2


def test_unfinished_bar_is_flagged(universe, cfg):
    data = {t: d.copy() for t, d in universe.items()}
    for d in data.values():
        d.iloc[-1, d.columns.get_loc("volume")] *= 0.1      # intraday snapshot: 10% of a day's volume
    assert any("unfinished" in w for w in run_scan(data, cfg).warnings)
    assert not any("unfinished" in w for w in run_scan(universe, cfg).warnings)


def test_stop_is_never_inside_todays_range():
    """A hammer: the long lower wick shows sellers already tested that level today."""
    row = pd.Series({"close": 100.0, "low": 94.0, "high": 100.5, "atr": 3.0, "st_dir": 1,
                     "st_line": 97.0, "breakout_recent": False, "pivot": np.nan})
    p = trade_plan(row, Config(), "long")
    assert p["stop"] <= 94.0 - 0.1 * 3.0 + 1e-9
    short = trade_plan(pd.Series({"close": 100.0, "low": 99.5, "high": 106.0, "atr": 3.0,
                                  "st_dir": -1, "st_line": 103.0}), Config(), "short")
    assert short["stop"] >= 106.0 + 0.1 * 3.0 - 1e-9


def test_loads_ibkr_price_history_shape(tmp_path):
    from smart_scanner.data import load
    bars = {"time": ["2026-10-19T13:30:00Z", "2026-10-20T13:30:00Z"], "open": [1, 2],
            "high": [2, 3], "low": [0.5, 1.5], "close": [1.5, 2.5], "volume": [100, 200]}
    p = tmp_path / "ibkr.json"
    p.write_text(__import__("json").dumps({"mtch": bars}))
    df = load(f"json:{p}")["MTCH"]
    assert str(df.index[-1].date()) == "2026-10-20" and df["close"].iloc[-1] == 2.5


def test_takeover_pinned_stock_is_skipped(universe, cfg):
    """After a deal is announced the price parks near the offer: a 'perfect tight base'
    that pattern rules love. It must be filtered out, not offered as a VCP."""
    df = universe["BRK"].copy()
    deal = df["close"].iloc[-60] * 1.3
    tail = np.full(59, deal) * (1 + 0.0005 * np.sin(np.arange(59)))
    df.iloc[-59:, df.columns.get_loc("close")] = tail
    df.iloc[-59:, df.columns.get_loc("open")] = tail
    df.iloc[-59:, df.columns.get_loc("high")] = tail * 1.001
    df.iloc[-59:, df.columns.get_loc("low")] = tail * 0.999
    data = {**universe, "TKO": df}
    res = run_scan(data, cfg)
    assert res.feats["TKO"]["pinned"].iloc[-1]
    assert "takeover" in res.skipped["TKO"]
    assert all("TKO" not in set(d["ticker"]) for d in (res.longs, res.watch, res.shorts) if not d.empty)
