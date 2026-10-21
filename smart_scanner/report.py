"""Self-contained HTML + CSV report (works offline, readable on a phone)."""
import html
from pathlib import Path

import numpy as np
import pandas as pd

GUIDE = {
    "RISK-ON": "Trend and breadth are healthy. Breakouts work best in this regime.",
    "MIXED": "Mixed signals. Be selective: only A/A+ setups, smaller size.",
    "RISK-OFF": "Market is weak. Most breakouts fail here. Prefer cash, puts or short setups; "
                "longs need an A+ score and half size.",
}
LONG_COLS = [("ticker", "Ticker"), ("grade", "Grade"), ("score", "Score"), ("setups", "Setups"),
             ("close", "Close"), ("day_pct", "Day %"), ("rs_rating", "RS"), ("rsi", "RSI"),
             ("adx", "ADX"), ("trend_template", "Trend 8"), ("stage", "Stage"),
             ("ext_atr", "Ext ATR"), ("rvol", "RVol"), ("stop", "Stop"), ("stop_pct", "Risk %"),
             ("target_2r", "Target 2R"), ("shares", "Shares"), ("position_usd", "Pos $"),
             ("fees_usd", "Fees $"), ("risk_usd", "Max loss $"), ("net_rr", "Net R:R"),
             ("earnings", "Earnings")]
WATCH_COLS = [("ticker", "Ticker"), ("score", "Score"), ("close", "Close"), ("alert_at", "Alert at"),
              ("pct_to_pivot", "% to pivot"), ("rs_rating", "RS"), ("rsi", "RSI"),
              ("trend_template", "Trend 8"), ("earnings", "Earnings")]


def _cell(k, v):
    if k == "shares" and isinstance(v, (int, float)) and not np.isnan(v):
        return f"{v:.3f}".rstrip("0").rstrip(".")
    return _fmt(v)


def _fmt(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    if isinstance(v, float):
        return f"{v:,.2f}".rstrip("0").rstrip(".") if abs(v) < 1000 else f"{v:,.0f}"
    return html.escape(str(v))


def _table(df: pd.DataFrame, cols, empty: str) -> str:
    if df is None or df.empty:
        return f'<p class="empty">{empty}</p>'
    cols = [(k, n) for k, n in cols if k in df.columns]
    head = "".join(f"<th>{n}</th>" for _, n in cols)
    rows = []
    for _, r in df.iterrows():
        cells = []
        for k, _ in cols:
            cls = ""
            if k == "grade":
                cls = f' class="g{str(r[k]).replace("+", "p")}"'
            if k == "day_pct" and isinstance(r[k], (int, float)) and not np.isnan(r[k]):
                cls = ' class="up"' if r[k] > 0 else ' class="dn"'
            cells.append(f"<td{cls}>{_cell(k, r[k])}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f'<div class="wrap"><table class="sortable"><thead><tr>{head}</tr></thead>' \
           f'<tbody>{"".join(rows)}</tbody></table></div>'


def build_html(res, title="Smart Scanner", backtest=None, universe_note="") -> str:
    label = res.regime_label.iloc[-1]
    checks = res.regime_checks.iloc[-1]
    check_html = "".join(f'<li class="{"ok" if v else "no"}">{"✓" if v else "✗"} {html.escape(k)}</li>'
                         for k, v in checks.items())
    asof = res.asof.date() if hasattr(res.asof, "date") else res.asof
    warnings = getattr(res, "warnings", None) or []
    warn_html = ("<div class='warn'><b>Check before acting</b><ul>"
                 + "".join(f"<li>{html.escape(w)}</li>" for w in warnings) + "</ul></div>") if warnings else ""
    bt_html = ""
    if backtest is not None and not backtest.summary.empty:
        s = backtest.summary.reset_index().rename(columns={"index": "group"})
        cols = [(c, c.replace("_", " ")) for c in s.columns]
        bt_html = (f"<h2>Backtest of these rules</h2><p class='note'>Baseline: an average stock-day "
                   f"returned {backtest.baseline_fwd20:.2f}% over the next 20 days. "
                   f"Win rate &lt;50% can still make money if average wins beat average losses.</p>"
                   + _table(s, cols, "No backtest trades."))
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<style>
:root{{--bg:#fff;--fg:#1d1d1f;--mut:#6e6e73;--line:#e5e5ea;--card:#f5f5f7;--up:#0a7d32;--dn:#c62828;
--on:#0a7d32;--mix:#b26a00;--off:#c62828}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111;--fg:#f2f2f2;--mut:#a1a1a6;--line:#2c2c2e;
--card:#1c1c1e;--up:#4cd964;--dn:#ff6b6b;--on:#4cd964;--mix:#ffb340;--off:#ff6b6b}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.45 -apple-system,Segoe UI,Roboto,sans-serif;
margin:0;padding:16px;max-width:1200px;margin:auto}}
h1{{font-size:22px;margin:0 0 4px}} h2{{font-size:18px;margin:28px 0 8px}}
.note,.empty{{color:var(--mut);font-size:13px}}
.regime{{background:var(--card);border-radius:12px;padding:14px;margin:16px 0}}
.warn{{border:1px solid var(--mix);border-radius:12px;padding:10px 14px;margin:12px 0;font-size:13px}}
.warn ul{{margin:6px 0 0;padding-left:18px}}
.badge{{font-weight:700;padding:3px 10px;border-radius:999px;color:#fff}}
.RISK-ON{{background:var(--on)}} .MIXED{{background:var(--mix)}} .RISK-OFF{{background:var(--off)}}
.regime ul{{list-style:none;padding:0;margin:8px 0 0;columns:2;font-size:13px}}
.ok{{color:var(--up)}} .no{{color:var(--dn)}}
.wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:10px}}
table{{border-collapse:collapse;width:100%;font-size:13px;white-space:nowrap}}
th,td{{padding:7px 9px;border-bottom:1px solid var(--line);text-align:right}}
th:first-child,td:first-child,td:nth-child(4),th:nth-child(4){{text-align:left}} th{{cursor:pointer;background:var(--card);position:sticky;top:0}}
td:first-child,th:first-child{{position:sticky;left:0;z-index:1;background:var(--bg);font-weight:600}}
th:first-child{{background:var(--card);z-index:2}}
.up{{color:var(--up)}} .dn{{color:var(--dn)}} .gAp{{color:var(--up);font-weight:700}} .gA{{color:var(--up)}}
@media (max-width:600px){{.regime ul{{columns:1}}}}
</style></head><body>
<h1>{html.escape(title)}</h1>
<div class="note">Data as of {asof} · {len(res.feats)} stocks scored {html.escape(universe_note)}</div>
{warn_html}
<div class="regime"><span class="badge {label}">{label}</span> {GUIDE[label]}<ul>{check_html}</ul></div>
<h2>Long setups (buy candidates)</h2>
<p class="note">Score 0–100 = trend 30% · momentum/RS 20% · volume 15% · setup trigger 20% · risk 15%,
adjusted for market regime. A+ also needs a real setup, RS 80+ and 7 of 8 trend rules.
Stop = where the trend counts as broken. Shares sized so hitting the stop loses your chosen
risk per trade.</p>
{_table(res.longs, LONG_COLS, "No stock passed today. Doing nothing is a valid result.")}
<h2>Watchlist: set a price alert</h2>
<p class="note">Strong trend and momentum, sitting just under a breakout level. Alert at the pivot,
then re-check volume when it triggers.</p>
{_table(res.watch, WATCH_COLS, "Nothing close to a breakout.")}
<h2>Short / put candidates</h2>
<p class="note">Weak trend, weak relative strength, breaking down. For puts or bear spreads, not
for buying.</p>
{_table(res.shorts, LONG_COLS, "No breakdowns today.")}
{bt_html}
<h2>How to read this</h2>
<p class="note"><b>RS</b> relative strength 1–99: rank vs every stock scanned (vs the S&amp;P 500 when
fewer than 100 are scanned) ·
<b>Trend 8</b> how many of Minervini's 8 trend-template rules pass ·
<b>Stage</b> Weinstein stage (2 = advancing, 4 = declining) ·
<b>Ext ATR</b> distance above the 50-day average in ATRs (above ~4 = stretched) ·
<b>RVol</b> today's volume vs 50-day average ·
<b>Max loss $</b> what you lose at the stop, commissions included ·
<b>Net R:R</b> what the 2R target pays after commissions (1.0 = gain equals the loss) · Not financial advice.</p>
<script>
document.querySelectorAll('table.sortable th').forEach((th,i)=>th.addEventListener('click',()=>{{
const tb=th.closest('table').tBodies[0];const asc=th.dataset.asc!=='1';th.dataset.asc=asc?'1':'0';
const val=t=>{{const x=parseFloat(t.replace(/[,%$]/g,''));return isNaN(x)?t:x}};
[...tb.rows].sort((a,b)=>{{const A=val(a.cells[i].innerText),B=val(b.cells[i].innerText);
return (A>B?1:A<B?-1:0)*(asc?1:-1)}}).forEach(r=>tb.appendChild(r))}}));
</script></body></html>"""


MD_TRADE_COLS = [("ticker", "Ticker"), ("grade", "Grade"), ("score", "Score"), ("setups", "Setups"),
                 ("close", "Close"), ("stop", "Stop"), ("stop_pct", "Risk %"), ("target_2r", "Target 2R"),
                 ("shares", "Shares"), ("risk_usd", "Max loss $"), ("net_rr", "Net R:R"),
                 ("rs_rating", "RS"), ("rvol", "RVol"), ("earnings", "Earnings")]


def _md_table(df: pd.DataFrame, cols, empty: str) -> str:
    if df is None or df.empty:
        return f"_{empty}_\n"
    cols = [(k, n) for k, n in cols if k in df.columns]
    esc = lambda x: html.unescape(str(x)).replace("|", "\\|")
    lines = ["| " + " | ".join(n for _, n in cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(esc(_cell(k, r[k])) for k, _ in cols) + " |")
    return "\n".join(lines) + "\n"


def build_markdown(res, title="Smart Scanner", backtest=None, universe_note="") -> str:
    """Same content as the HTML report as Markdown, which GitHub renders (also in its phone app)."""
    label = res.regime_label.iloc[-1]
    checks = res.regime_checks.iloc[-1]
    asof = res.asof.date() if hasattr(res.asof, "date") else res.asof
    out = [f"# {title}\n", f"Data as of {asof} · {len(res.feats)} stocks scored {universe_note}\n"]
    warnings = getattr(res, "warnings", None) or []
    if warnings:
        out.append("> **Check before acting**\n" + "".join(f"> - {w}\n" for w in warnings))
    out.append(f"**Market: {label}.** {GUIDE[label]}\n")
    out.append(" · ".join(f"{'✅' if v else '❌'} {k}" for k, v in checks.items()) + "\n")
    out.append("## Long setups (buy candidates)\n")
    out.append(_md_table(res.longs, MD_TRADE_COLS, "No stock passed today. Doing nothing is a valid result."))
    out.append("## Watchlist: set a price alert at the pivot\n")
    out.append(_md_table(res.watch, WATCH_COLS, "Nothing close to a breakout."))
    out.append("## Short / put candidates\n")
    out.append(_md_table(res.shorts, MD_TRADE_COLS, "No breakdowns today."))
    if backtest is not None and not backtest.summary.empty:
        s = backtest.summary.reset_index().rename(columns={"index": "group"})
        out.append("## Backtest of these rules\n")
        out.append(f"Baseline: an average stock-day returned {backtest.baseline_fwd20:.2f}% over the next 20 days.\n")
        out.append(_md_table(s, [(c, c.replace("_", " ")) for c in s.columns], "No backtest trades."))
    out.append("\n**Max loss $** includes commissions · **Net R:R** is what the 2R target pays after "
               "commissions · RS 1–99 relative strength · Not financial advice.\n")
    return "\n".join(out)


def save_report(res, out_dir: str, backtest=None, universe_note="") -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = str(res.asof.date() if hasattr(res.asof, "date") else res.asof)
    html_path = out / f"scan_{stamp}.html"
    html_path.write_text(build_html(res, f"Smart Scanner · {stamp}", backtest, universe_note), encoding="utf-8")
    md_path = out / f"scan_{stamp}.md"
    md_path.write_text(build_markdown(res, f"Smart Scanner · {stamp}", backtest, universe_note), encoding="utf-8")
    paths = {"html": str(html_path), "md": str(md_path)}
    for name in ("longs", "shorts", "watch"):
        df = getattr(res, name)
        if df is not None and not df.empty:
            p = out / f"{name}_{stamp}.csv"
            df.to_csv(p, index=False)
            paths[name] = str(p)
    return paths
