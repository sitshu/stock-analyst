from __future__ import annotations
from datetime import timedelta
from typing import List, Tuple
import pandas as pd
import numpy as np

from ..models import EarningsEvent, ReactionItem, ReactionResponse, ReactionSummary
from ..sources.prices_yfinance import get_earnings_dates, get_price_history, get_revenue_data

def _normalize_earnings_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "report_date","eps_estimate","eps_actual","surprise_pct"
        ])
    
    # Reset index to make date a column
    df_reset = df.reset_index()
    
    out = pd.DataFrame()
    
    # Handle earnings date
    if "Earnings Date" in df_reset.columns:
        out["report_date"] = pd.to_datetime(df_reset["Earnings Date"], errors="coerce").dt.date
    else:
        out["report_date"] = None
        
    # Handle EPS columns
    out["eps_estimate"] = pd.to_numeric(df_reset.get("EPS Estimate"), errors="coerce") if "EPS Estimate" in df_reset.columns else None
    out["eps_actual"] = pd.to_numeric(df_reset.get("Reported EPS"), errors="coerce") if "Reported EPS" in df_reset.columns else None
    out["surprise_pct"] = pd.to_numeric(df_reset.get("Surprise(%)"), errors="coerce") if "Surprise(%)" in df_reset.columns else None
    
    out = out.dropna(subset=["report_date"])
    return out.sort_values("report_date", ascending=False)

def get_earnings_events(ticker: str, limit: int = 12) -> List[EarningsEvent]:
    df = _normalize_earnings_df(get_earnings_dates(ticker, limit=limit))
    
    # Get revenue data
    revenue_data = get_revenue_data(ticker)
    rev_estimates = revenue_data.get('estimates')
    rev_actuals = revenue_data.get('actuals')
    
    events: List[EarningsEvent] = []
    for _, r in df.iterrows():
        revenue_actual = None
        revenue_estimate = None
        revenue_surprise_pct = None
        
        if rev_actuals is not None and rev_estimates is not None:
            try:
                report_date = pd.to_datetime(r["report_date"])
                
                # Match actual revenue by finding closest quarter end
                if hasattr(rev_actuals, 'index'):
                    quarter_ends = pd.to_datetime(rev_actuals.index)
                    # Find the quarter end closest to but before/at the earnings date
                    valid_quarters = quarter_ends[quarter_ends <= report_date + pd.Timedelta(days=45)]
                    if len(valid_quarters) > 0:
                        closest_quarter = valid_quarters.max()
                        revenue_actual = float(rev_actuals[closest_quarter]) / 1e9
                
                # Match estimate by quarter timing
                if not rev_estimates.empty:
                    # For recent dates, use current quarter (0q), for older dates use year-ago data
                    days_ago = (pd.Timestamp.now() - report_date).days
                    if days_ago < 120:  # Recent quarter
                        if '0q' in rev_estimates.index:
                            revenue_estimate = float(rev_estimates.loc['0q', 'avg']) / 1e9
                    else:  # Use year-ago revenue as proxy estimate
                        if '0q' in rev_estimates.index and 'yearAgoRevenue' in rev_estimates.columns:
                            revenue_estimate = float(rev_estimates.loc['0q', 'yearAgoRevenue']) / 1e9
                
                # Calculate surprise
                if revenue_actual and revenue_estimate:
                    revenue_surprise_pct = ((revenue_actual - revenue_estimate) / revenue_estimate) * 100
                    
            except Exception:
                pass
        
        events.append(EarningsEvent(
            fiscal_quarter=None,
            report_date=r["report_date"],
            eps_actual=(None if pd.isna(r["eps_actual"]) else float(r["eps_actual"])),
            eps_estimate=(None if pd.isna(r["eps_estimate"]) else float(r["eps_estimate"])),
            eps_surprise_pct=(None if pd.isna(r["surprise_pct"]) else float(r["surprise_pct"])),
            revenue_actual=revenue_actual,
            revenue_estimate=revenue_estimate,
            revenue_surprise_pct=revenue_surprise_pct,
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
