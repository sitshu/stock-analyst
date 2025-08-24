from __future__ import annotations
from typing import Optional
from ..models import TickerProfile
from ..sources.prices_yfinance import get_info

def build_profile(ticker: str) -> TickerProfile:
    info = get_info(ticker)

    pfcf = None
    try:
        mcap = info.get("marketCap")
        fcf = info.get("freeCashflow")
        if mcap and fcf and fcf > 0:
            pfcf = float(mcap) / float(fcf)
    except Exception:
        pfcf = None

    ev_ebitda = None
    try:
        ev = info.get("enterpriseValue")
        ebitda = info.get("ebitda")
        if ev and ebitda and ebitda > 0:
            ev_ebitda = float(ev) / float(ebitda)
    except Exception:
        ev_ebitda = None

    return TickerProfile(
        ticker=ticker.upper(),
        name=info.get("shortName") or info.get("longName"),
        sector=info.get("sector"),
        industry=info.get("industry"),
        market_cap=info.get("marketCap"),
        price=info.get("currentPrice"),
        pe=info.get("trailingPE") or info.get("forwardPE"),
        pfcf=pfcf,
        ev_ebitda=ev_ebitda,
        gross_margin=info.get("grossMargins"),
        profit_margin=info.get("profitMargins"),
        description=info.get("longBusinessSummary"),
    )
