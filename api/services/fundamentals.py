# api/services/fundamentals.py
from __future__ import annotations
from typing import Optional
from ..models import TickerProfile
from ..sources.prices_yfinance import (
    get_info,
    get_fast_info,
    get_last_price_from_history,
)

def _first_non_none(*vals):
    for v in vals:
        if v is not None:
            return v
    return None

def build_profile(ticker: str) -> TickerProfile:
    ticker = ticker.upper()

    # Gather all sources
    info = get_info(ticker)           # description/sector/industry (may be empty)
    fast = get_fast_info(ticker)      # last_price, market_cap, shares_outstanding (often reliable)

    # Price
    price = _first_non_none(
        fast.get("last_price"),
        fast.get("last_close"),
        info.get("currentPrice"),
        get_last_price_from_history(ticker),   # robust fallback
    )

    # Market cap
    market_cap = _first_non_none(
        fast.get("market_cap"),
        info.get("marketCap"),
        # derive market cap if we have shares outstanding and a price
        (float(fast.get("shares_outstanding")) * float(price)) if fast.get("shares_outstanding") and price else None,
    )

    # P/E
    pe = _first_non_none(info.get("trailingPE"), info.get("forwardPE"))

    # P/FCF (best effort)
    pfcf = None
    try:
        fcf = info.get("freeCashflow")
        if market_cap and fcf and float(fcf) > 0:
            pfcf = float(market_cap) / float(fcf)
    except Exception:
        pfcf = None

    # EV/EBITDA (best effort)
    ev_ebitda = None
    try:
        ev = info.get("enterpriseValue")
        ebitda = info.get("ebitda")
        if ev and ebitda and float(ebitda) > 0:
            ev_ebitda = float(ev) / float(ebitda)
    except Exception:
        ev_ebitda = None

    # Margins (may be None if info is empty)
    gross_margin = info.get("grossMargins")
    profit_margin = info.get("profitMargins")

    return TickerProfile(
        ticker=ticker,
        name=_first_non_none(info.get("shortName"), info.get("longName")),
        sector=info.get("sector"),
        industry=info.get("industry"),
        market_cap=market_cap,
        price=price,
        pe=pe,
        pfcf=pfcf,
        ev_ebitda=ev_ebitda,
        gross_margin=gross_margin,
        profit_margin=profit_margin,
        description=info.get("longBusinessSummary"),
    )
