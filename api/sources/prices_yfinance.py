from __future__ import annotations
import pandas as pd
import yfinance as yf

def get_info(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    try:
        info = t.get_info()
    except Exception:
        info = t.info or {}
    return info or {}

def get_price_history(ticker: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if not df.empty:
        df = df.rename(columns={c: c.capitalize() for c in df.columns})
    return df

def get_earnings_dates(ticker: str, limit: int = 12) -> pd.DataFrame:
    t = yf.Ticker(ticker)
    try:
        df = t.get_earnings_dates(limit=limit)
    except Exception:
        df = pd.DataFrame()
    return df if df is not None else pd.DataFrame()
