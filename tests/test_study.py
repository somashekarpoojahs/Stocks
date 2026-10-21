import numpy as np
import pandas as pd
import pytest

from smart_scanner.study import EXITS, Exit, build_markdown, run_study, simulate


def path(closes, st_dir=1, atr=1.0):
    c = list(map(float, closes))
    n = len(c)
    return {"open": c[:], "high": [x * 1.001 for x in c], "low": [x * 0.999 for x in c], "close": c,
            "atr": [atr] * n, "st_line": [x - 3 for x in c], "st_dir": [float(st_dir)] * n,
            "ema21": [x - 2 for x in c], "sma50": [x - 4 for x in c]}


def test_fixed_target_pays_2r():
    px = path(np.linspace(100, 130, 40))
    R, bars, why = simulate(px, 1, px["open"][1], 5.0, Exit("t", target_r=2.0, max_hold=40), cost=0)
    assert why == "target" and R == pytest.approx(2.0)


def test_trailing_exit_rides_the_trend():
    px = path(np.linspace(100, 160, 80))
    R, bars, why = simulate(px, 1, px["open"][1], 5.0, Exit("trail", max_hold=60, trail="chandelier"), cost=0)
    assert why == "time" and R > 8                      # 60 days of uptrend, never stopped


def test_gap_through_stop_fills_at_open():
    closes = [100, 100, 100, 90, 90]
    px = path(closes)
    R, bars, why = simulate(px, 1, 100.0, 5.0, Exit("t", target_r=2.0, max_hold=20), cost=0)
    assert why == "stop" and R == pytest.approx(-2.0)   # opened at 90, two stops below entry


def test_supertrend_exit_waits_until_armed():
    """Bought while Supertrend still pointed down: no instant exit; it arms once up."""
    px = path(np.linspace(100, 120, 30), st_dir=-1)
    out = simulate(px, 1, px["open"][1], 5.0, Exit("st", max_hold=20, trail="supertrend"), cost=0)
    assert out[2] == "time" and out[1] == 20


def test_half_at_2r_banks_half():
    closes = list(np.linspace(100, 111, 12)) + [111] * 3 + [95] * 5
    px = path(closes)
    R, _, why = simulate(px, 1, 100.0, 5.0, Exit("half", max_hold=60, half_at_r=2.0), cost=0)
    assert why == "stop" and R == pytest.approx(0.5 * 2.0 + 0.5 * -1.0, abs=0.05)


def test_study_end_to_end(universe, cfg):
    res = run_study(universe, cfg, threshold=60)
    assert list(res.summary.index) == [e.name for e in EXITS if e.name in res.summary.index]
    assert {"avg_R", "random_avg_R", "edge_R", "R_per_20_days"} <= set(res.summary.columns)
    assert set(res.trades["kind"]) <= {"signal", "random"}
    md = build_markdown(res, "test")
    assert "## Verdict" in md and "Best exit" in md
