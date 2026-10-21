"""Which tickers to scan. 'sp1500' = S&P 500 + 400 + 600 (~1,500 US stocks)."""
import io
from pathlib import Path

import pandas as pd

SP500_CSV = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
WIKI = {
    "sp400": "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies",
    "sp600": "https://en.wikipedia.org/wiki/List_of_S%26P_600_companies",
    "nasdaq100": "https://en.wikipedia.org/wiki/Nasdaq-100",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (smart-scanner; personal research)"}


def _yahoo(sym: str) -> str:
    return str(sym).strip().upper().replace(".", "-")


def _wiki_symbols(url: str) -> list:
    import requests

    page = requests.get(url, headers=HEADERS, timeout=30).text
    for table in pd.read_html(io.StringIO(page)):
        for col in ("Symbol", "Ticker", "Ticker symbol"):
            if col in table.columns:
                return table[col].astype(str).tolist()
    raise ValueError(f"No ticker column found at {url}")


def sp500() -> list:
    return pd.read_csv(SP500_CSV)["Symbol"].astype(str).tolist()


def get_universe(spec: str) -> list:
    spec = spec.strip()
    if spec.lower().startswith("file:"):
        syms = [s for s in Path(spec[5:]).read_text().split() if s and not s.startswith("#")]
    elif "," in spec or spec.isupper():
        syms = spec.split(",")
    else:
        key = spec.lower()
        parts = {"sp500": ["sp500"], "sp400": ["sp400"], "sp600": ["sp600"],
                 "nasdaq100": ["nasdaq100"], "sp1500": ["sp500", "sp400", "sp600"],
                 "all": ["sp500", "sp400", "sp600", "nasdaq100"]}[key]
        syms = []
        for p in parts:
            syms += sp500() if p == "sp500" else _wiki_symbols(WIKI[p])
    return sorted({_yahoo(s) for s in syms if s and s.lower() != "nan"})
