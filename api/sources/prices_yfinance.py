# api/sources/prices_yfinance.py
from __future__ import annotations

import datetime as dt
from typing import Optional

import yfinance as yf
from ..util.http import get_session, reset_session  # http.py lives in api/util/

_session = None


def _yf_session():
    global _session
    if _session is None:
        # requests-compatible session; supports curl_cffi TLS impersonation if enabled
        _session = get_session()
    return _session


# ---------- Prices (download-based, robust) ----------

def get_last_price_from_history(symbol: str) -> Optional[float]:
    """Return the most recent close using yf.download()."""
    df = yf.download(
        symbol.upper(),
        period="5d",
        interval="1d",
        progress=False,
        session=_yf_session(),
    )
    if df.empty:
        return None
    return float(df["Close"].dropna().iloc[-1])


def get_history(symbol: str, period: str = "1mo", interval: str = "1d"):
    """Convenience wrapper for recent history."""
    return yf.download(
        symbol.upper(),
        period=period,
        interval=interval,
        progress=False,
        session=_yf_session(),
    )


def get_price_history(
    symbol: str,
    *,
    start: Optional[str | dt.date] = None,
    end: Optional[str | dt.date] = None,
    period: Optional[str] = "1y",
    interval: str = "1d",
):
    """
    Flexible history accessor used by earnings code.
    If start/end provided -> use them; else use period.
    """
    kwargs = dict(
        tickers=symbol.upper(),
        interval=interval,
        progress=False,
        session=_yf_session(),
    )
    if start or end:
        kwargs.update(start=start, end=end)
    else:
        kwargs.update(period=period or "1y")

    return yf.download(**kwargs)


# ---------- Fundamentals-ish (best-effort; may require impersonation) ----------

def get_info(symbol: str) -> dict:
    """
    Returns Ticker.info as a dict or {} on failure.
    This still hits Yahoo’s quoteSummary; works best with TLS impersonation.
    """
    try:
        t = yf.Ticker(symbol.upper(), session=_yf_session())
        return dict(getattr(t, "info", {}) or {})
    except Exception:
        return {}


def get_fast_info(symbol: str) -> dict:
    """
    Returns Ticker.fast_info as a dict or {} on failure.
    """
    try:
        t = yf.Ticker(symbol.upper(), session=_yf_session())
        return dict(getattr(t, "fast_info", {}) or {})
    except Exception:
        return {}


# ---------- Earnings (yfinance helper) ----------

def get_revenue_data(symbol: str):
    """
    Get revenue estimates and actuals for earnings analysis.
    Returns dict with estimates and actuals.
    """
    try:
        t = yf.Ticker(symbol.upper(), session=_yf_session())
        
        # Get revenue estimates
        rev_est = t.get_revenue_estimate()
        
        # Get actual revenue from quarterly financials
        qf = t.quarterly_financials
        actual_revenue = None
        if not qf.empty and 'Total Revenue' in qf.index:
            actual_revenue = qf.loc['Total Revenue']
            
        return {
            'estimates': rev_est if not rev_est.empty else None,
            'actuals': actual_revenue if actual_revenue is not None else None
        }
    except Exception:
        return {'estimates': None, 'actuals': None}


def get_earnings_dates(symbol: str, limit: int = 12):
    """
    Return upcoming/past earnings dates as a DataFrame (yfinance format).
    Columns typically include: 'Earnings Date', 'EPS Estimate', 'Reported EPS', 'Surprise(%)'.
    NOTE: This may still rely on endpoints that benefit from TLS impersonation.
    """
    try:
        t = yf.Ticker(symbol.upper(), session=_yf_session())
        # yfinance API: get_earnings_dates(limit=...)
        return t.get_earnings_dates(limit=limit)
    except Exception:
        # Return an empty DataFrame with expected columns shape, so callers don't explode.
        import pandas as pd
        return pd.DataFrame(columns=["Earnings Date", "EPS Estimate", "Reported EPS", "Surprise(%)"])
