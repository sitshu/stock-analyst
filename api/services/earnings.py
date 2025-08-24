from __future__ import annotations
from datetime import timedelta
from typing import List, Tuple
import pandas as pd
import numpy as np

from ..models import EarningsEvent, ReactionItem, ReactionResponse, ReactionSummary
from ..sources.prices_yfinance import get_earnings_dates, get_price_history

def _normalize_earnings_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "report_date","eps_estimate","eps_actual","surprise_pct"
        ])
    cols = {c.lower().strip(): c for c in df.columns}
    out = pd.DataFrame()
    out["report_date"] = pd.to_datetime(df.get("Earnings Date") or df.get(cols.get("earnings date")), errors="coerce").dt.date
    out["eps_estimate"] = pd.to_numeric(df.get("EPS Estimate") or df.get(cols.get("eps estimate")), errors="coerce")
    out["eps_actual"] = pd.to_numeric(df.get("Reported EPS") or df.get(cols.get("reported eps")), errors="coerce")
    out["surprise_pct"] = pd.to_numeric(df.get("Surprise(%)") or df.get(cols.get("surprise(%)")), errors="coerce")
    out = out.dropna(subset=["report_date"])
    return out.sort_values("report_date", ascending=False)

def get_earnings_events(ticker: str, limit: int = 12) -> List[EarningsEvent]:
    df = _normalize_earnings_df(get_earnings_dates(ticker, limit=limit))
    events: List[EarningsEvent] = []
    for _, r in df.iterrows():
        events.append(EarningsEvent(
            fiscal_quarter=None,
            report_date=r["report_date"],
            eps_actual=(None if pd.isna(r["eps_actual"]) else float(r["eps_actual"])),
            eps_estimate=(None if pd.isna(r["eps_estimate"]) else float(r["eps_estimate"])),
            eps_surprise_pct=(None if pd.isna(r["surprise_pct"]) else float(r["surprise_pct"])),
            revenue_actual=None,
            revenue_estimate=None,
            revenue_surprise_pct=None,
        ))
    return events

def _returns_around_dates(prices: pd.DataFrame, dates: List[pd.Timestamp]) -> Tuple[List[float], List[float], List[float]]:
    prices = prices.copy()
    prices.index = pd.to_datetime(prices.index)
    prices["ret"] = prices["Close"].pct_change()
    vol = prices["ret"].rolling(20).std() * np.sqrt(252)
    vol_pct = vol * 100.0

    next_day, five_day, baseline = [], [], []
    for d in dates:
        d = pd.to_datetime(d)
        if d not in prices.index:
            future = prices.index[prices.index >= d]
            if len(future) == 0:
                continue
            d = future[0]
        idx = prices.index.get_loc(d)
        if idx + 1 < len(prices):
            c0 = float(prices["Close"].iloc[idx])
            c1 = float(prices["Close"].iloc[idx + 1])
            next_day.append((c1 / c0 - 1.0) * 100.0)
        else:
            next_day.append(np.nan)
        if idx + 5 < len(prices):
            c5 = float(prices["Close"].iloc[idx + 5])
            five_day.append((c5 / c0 - 1.0) * 100.0)
        else:
            five_day.append(np.nan)
        baseline.append(float(vol_pct.iloc[max(0, idx - 1)]))
    return next_day, five_day, baseline

def earnings_reaction(ticker: str, limit: int = 12) -> ReactionResponse:
    events = get_earnings_events(ticker, limit=limit)
    if not events:
        return ReactionResponse(ticker=ticker.upper(), items=[], summary=ReactionSummary())

    dates = sorted({e.report_date for e in events})
    start = (min(dates) - timedelta(days=20)).isoformat()
    prices = get_price_history(ticker, start=start, end=None)
    if prices is None or prices.empty:
        items = [ReactionItem(report_date=e.report_date) for e in events]
        return ReactionResponse(ticker=ticker.upper(), items=items, summary=ReactionSummary())

    date_stamps = [pd.Timestamp(d) for d in dates]
    nd, fd, base = _returns_around_dates(prices, date_stamps)

    items: List[ReactionItem] = []
    for e, r1, r5, b in zip(events, nd[::-1], fd[::-1], base[::-1]):
        items.append(ReactionItem(
            report_date=e.report_date,
            next_day_return_pct=(None if pd.isna(r1) else float(r1)),
            five_day_return_pct=(None if pd.isna(r5) else float(r5)),
            baseline_volatility_pct=(None if pd.isna(b) else float(b)),
        ))

    valid_moves = [i.next_day_return_pct for i in items if i.next_day_return_pct is not None]
    up = [x for x in valid_moves if x >= 0]
    down = [x for x in valid_moves if x < 0]
    avg_abs = float(np.nan) if not valid_moves else float(np.mean([abs(x) for x in valid_moves]))

    beats = sum(1 for e in events if (e.eps_surprise_pct is not None and e.eps_surprise_pct > 0))
    misses = sum(1 for e in events if (e.eps_surprise_pct is not None and e.eps_surprise_pct < 0))

    summary = ReactionSummary(
        average_upside_pct=(float(np.mean(up)) if up else None),
        average_downside_pct=(float(np.mean(down)) if down else None),
        average_abs_move_pct=(avg_abs if valid_moves else None),
        beats_count=beats or None,
        misses_count=misses or None,
    )
    return ReactionResponse(ticker=ticker.upper(), items=items[::-1], summary=summary)
