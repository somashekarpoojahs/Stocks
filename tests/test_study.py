import numpy as np
import pandas as pd
import pytest

from smart_scanner.study import EXITS, Exit, build_markdown, run_study, simulate


def path(closes, st_dir=1, atr=1.0):
    c = list(map(float, closes))
    n = len(c)
    return {"open": c[:], "high": [x * 1.001 for x in c], "low": [x * 0.999 for x in c], "close": c,
            "atr": [atr] * n, "st_line": [x - 3 for x in c], "st_dir": [float(st_dir)] * n,
            "st7_line": [x - 2 for x in c], "st7_dir": [float(st_dir)] * n,
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


def test_supertrend7_exit_sells_the_open_after_the_flip_down():
    px = path(np.linspace(100, 110, 30))
    px["st7_dir"][10:] = [-1.0] * 20                      # turns down at the close of bar 10
    R, bars, why = simulate(px, 1, px["open"][1], 5.0, Exit("st7", max_hold=60, trail="supertrend7"), cost=0)
    assert why == "trail" and bars == 11
    assert R == pytest.approx((px["open"][11] - px["open"][1]) / 5.0)


@pytest.mark.parametrize("entry", ["restart", "st7_flip"])
def test_study_supertrend_entries(universe, cfg, entry):
    res = run_study(universe, cfg, entry=entry)
    assert res.entry == entry
    md = build_markdown(res, "test")
    if entry == "st7_flip":                                # random walks flip all the time
        assert "Trail Supertrend (7, 3), 120 days" in res.summary.index
        assert (res.trades.loc[res.trades["kind"] == "signal", "setup"] == "st7_flip").all()
        assert "chart's own exit" in md and "relative strength" in md


def test_study_rejects_unknown_entry(universe, cfg):
    with pytest.raises(ValueError):
        run_study(universe, cfg, entry="nope")


def test_close_below_supertrend7_ignores_intraday_pokes():
    """The chart's sell arrow needs a daily close below the line; a stop order at the
    line sells on the first intraday touch."""
    px = path([100] * 30)
    px["low"][5] = px["st7_line"][4] - 0.5               # one intraday poke through the line
    px["st7_dir"][12:] = [-1.0] * 18                      # first close below it: bar 12
    stop_order = simulate(px, 1, 100.0, 5.0, Exit("a", max_hold=60, trail="supertrend7"), cost=0)
    on_close = simulate(px, 1, 100.0, 5.0, Exit("b", max_hold=60, trail="supertrend7_close"), cost=0)
    assert stop_order[1:] == (5, "stop") and on_close[1:] == (13, "trail")
