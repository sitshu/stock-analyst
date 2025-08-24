from __future__ import annotations
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import pandas as pd
import numpy as np

from ..models import EarningsEvent, ReactionResponse
from .earnings import get_earnings_events, earnings_reaction
from .fundamentals import build_profile
from ..sources.prices_yfinance import get_price_history

def get_earnings_risk_metrics(ticker: str) -> Dict:
    """Calculate risk metrics for position sizing"""
    reaction = earnings_reaction(ticker)
    items = reaction.items
    
    if not items:
        return {"avg_move": 0, "max_move": 0, "volatility": 0, "win_rate": 0}
    
    moves = [abs(i.next_day_return_pct) for i in items if i.next_day_return_pct is not None]
    positive_moves = [i.next_day_return_pct for i in items if i.next_day_return_pct and i.next_day_return_pct > 0]
    
    if not moves:
        return {"avg_move": 0, "max_move": 0, "volatility": 0, "win_rate": 0}
    
    return {
        "avg_move": float(np.mean(moves)),
        "max_move": float(max(moves)),
        "volatility": float(np.std(moves)),
        "win_rate": len(positive_moves) / len(moves) if moves else 0,
        "sample_size": len(moves)
    }

def get_surprise_signal(event: EarningsEvent) -> str:
    """Generate trading signal based on earnings surprises"""
    eps_beat = event.eps_surprise_pct and event.eps_surprise_pct > 0
    rev_beat = event.revenue_surprise_pct and event.revenue_surprise_pct > 0
    
    if eps_beat and rev_beat:
        return "STRONG_BUY"
    elif eps_beat or rev_beat:
        return "WEAK_BUY"
    elif event.eps_surprise_pct and event.eps_surprise_pct < -5:
        return "SELL"
    else:
        return "HOLD"

def get_upcoming_earnings(days_ahead: int = 7) -> List[Dict]:
    """Get earnings calendar for next N days (simplified - would need real calendar data)"""
    # This is a placeholder - in practice you'd integrate with earnings calendar API
    return []

def export_trading_data(tickers: List[str]) -> pd.DataFrame:
    """Export earnings and reaction data for external trading systems"""
    all_data = []
    
    for ticker in tickers:
        try:
            events = get_earnings_events(ticker, limit=8)
            reaction = earnings_reaction(ticker)
            risk_metrics = get_earnings_risk_metrics(ticker)
            
            for event in events:
                # Find matching reaction data
                reaction_item = next((r for r in reaction.items if r.report_date == event.report_date), None)
                
                all_data.append({
                    "ticker": ticker,
                    "date": event.report_date,
                    "eps_actual": event.eps_actual,
                    "eps_estimate": event.eps_estimate,
                    "eps_surprise_pct": event.eps_surprise_pct,
                    "revenue_actual": event.revenue_actual,
                    "revenue_estimate": event.revenue_estimate,
                    "revenue_surprise_pct": event.revenue_surprise_pct,
                    "next_day_return_pct": reaction_item.next_day_return_pct if reaction_item else None,
                    "five_day_return_pct": reaction_item.five_day_return_pct if reaction_item else None,
                    "signal": get_surprise_signal(event),
                    "avg_volatility": risk_metrics["avg_move"],
                    "win_rate": risk_metrics["win_rate"]
                })
        except Exception:
            continue
    
    return pd.DataFrame(all_data)

def check_trading_alerts(watchlist: List[str]) -> List[Dict]:
    """Check for trading alerts based on fundamental and earnings criteria"""
    alerts = []
    
    for ticker in watchlist:
        try:
            profile = build_profile(ticker)
            events = get_earnings_events(ticker, limit=1)
            risk_metrics = get_earnings_risk_metrics(ticker)
            
            # Value alert
            if profile.pe and profile.pe < 15 and profile.profit_margin and profile.profit_margin > 0.2:
                alerts.append({
                    "ticker": ticker,
                    "type": "VALUE_OPPORTUNITY",
                    "message": f"Undervalued: P/E {profile.pe:.1f}, Margin {profile.profit_margin*100:.1f}%"
                })
            
            # High volatility alert
            if risk_metrics["avg_move"] > 8:
                alerts.append({
                    "ticker": ticker,
                    "type": "HIGH_VOLATILITY",
                    "message": f"High earnings volatility: {risk_metrics['avg_move']:.1f}% avg move"
                })
            
            # Upcoming earnings alert (simplified)
            if events:
                days_to_earnings = (events[0].report_date - date.today()).days
                if 0 <= days_to_earnings <= 5:
                    alerts.append({
                        "ticker": ticker,
                        "type": "EARNINGS_SOON",
                        "message": f"Earnings in {days_to_earnings} days, avg move: {risk_metrics['avg_move']:.1f}%"
                    })
                    
        except Exception:
            continue
    
    return alerts
