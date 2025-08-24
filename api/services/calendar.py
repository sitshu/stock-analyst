from __future__ import annotations
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import pandas as pd

from .earnings import get_earnings_events
from .trading import get_earnings_risk_metrics

def get_earnings_calendar(days_ahead: int = 14, tickers: List[str] = None) -> List[Dict]:
    """Get upcoming earnings for specified tickers or watchlist"""
    if tickers is None:
        # Default watchlist of popular stocks
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "CRM", "ORCL"]
    
    calendar_events = []
    today = date.today()
    cutoff_date = today + timedelta(days=days_ahead)
    
    for ticker in tickers:
        try:
            events = get_earnings_events(ticker, limit=4)
            risk_metrics = get_earnings_risk_metrics(ticker)
            
            for event in events:
                if not event.report_date:
                    continue
                    
                # Check if earnings is upcoming
                if today <= event.report_date <= cutoff_date:
                    days_until = (event.report_date - today).days
                    
                    calendar_events.append({
                        "ticker": ticker,
                        "report_date": event.report_date,
                        "days_until": days_until,
                        "eps_estimate": event.eps_estimate,
                        "revenue_estimate": event.revenue_estimate,
                        "avg_move_pct": risk_metrics.get("avg_move", 0),
                        "max_move_pct": risk_metrics.get("max_move", 0),
                        "win_rate": risk_metrics.get("win_rate", 0),
                        "volatility": risk_metrics.get("volatility", 0)
                    })
                    
        except Exception:
            continue
    
    # Sort by days until earnings
    calendar_events.sort(key=lambda x: x["days_until"])
    return calendar_events

def get_sector_comparison(ticker: str, sector_tickers: List[str] = None) -> Dict:
    """Compare ticker against sector peers"""
    if sector_tickers is None:
        # Default tech sector comparison
        sector_map = {
            "AAPL": ["MSFT", "GOOGL", "META", "AMZN"],
            "MSFT": ["AAPL", "GOOGL", "META", "ORCL"],
            "GOOGL": ["AAPL", "MSFT", "META", "AMZN"],
            "TSLA": ["F", "GM", "RIVN", "LCID"],
            "NVDA": ["AMD", "INTC", "QCOM", "AVGO"]
        }
        sector_tickers = sector_map.get(ticker.upper(), ["SPY"])  # Default to SPY if no peers
    
    comparison_data = []
    
    # Add the main ticker first
    all_tickers = [ticker] + sector_tickers
    
    for t in all_tickers:
        try:
            risk_metrics = get_earnings_risk_metrics(t)
            events = get_earnings_events(t, limit=1)
            
            # Get next earnings date
            next_earnings = None
            if events:
                next_earnings = events[0].report_date
                if next_earnings and next_earnings < date.today():
                    next_earnings = None
            
            comparison_data.append({
                "ticker": t.upper(),
                "is_target": t.upper() == ticker.upper(),
                "avg_move_pct": risk_metrics.get("avg_move", 0),
                "max_move_pct": risk_metrics.get("max_move", 0),
                "win_rate": risk_metrics.get("win_rate", 0),
                "volatility": risk_metrics.get("volatility", 0),
                "sample_size": risk_metrics.get("sample_size", 0),
                "next_earnings": next_earnings.strftime("%Y-%m-%d") if next_earnings else None
            })
            
        except Exception:
            continue
    
    if not comparison_data:
        return {"error": "No comparison data available"}
    
    # Calculate sector averages (excluding the target ticker)
    peer_data = [d for d in comparison_data if not d["is_target"]]
    if peer_data:
        sector_avg = {
            "avg_move_pct": sum(d["avg_move_pct"] for d in peer_data) / len(peer_data),
            "max_move_pct": sum(d["max_move_pct"] for d in peer_data) / len(peer_data),
            "win_rate": sum(d["win_rate"] for d in peer_data) / len(peer_data),
            "volatility": sum(d["volatility"] for d in peer_data) / len(peer_data)
        }
    else:
        sector_avg = {"avg_move_pct": 0, "max_move_pct": 0, "win_rate": 0, "volatility": 0}
    
    return {
        "target_ticker": ticker.upper(),
        "comparison_data": comparison_data,
        "sector_averages": sector_avg,
        "peer_count": len(peer_data)
    }

def get_high_volatility_calendar(min_avg_move: float = 5.0, days_ahead: int = 14) -> List[Dict]:
    """Get upcoming earnings for high volatility stocks"""
    calendar = get_earnings_calendar(days_ahead)
    
    # Filter for high volatility stocks
    high_vol_events = [
        event for event in calendar 
        if event["avg_move_pct"] >= min_avg_move
    ]
    
    # Sort by volatility descending
    high_vol_events.sort(key=lambda x: x["avg_move_pct"], reverse=True)
    
    return high_vol_events
