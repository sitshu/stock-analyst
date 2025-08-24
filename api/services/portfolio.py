from __future__ import annotations
from datetime import datetime, date
from typing import List, Dict, Optional
import pandas as pd

from .technical import get_technical_signals
from .trading import get_earnings_risk_metrics
from ..sources.prices_yfinance import get_last_price_from_history

class Position:
    def __init__(self, ticker: str, shares: float, entry_price: float, entry_date: str):
        self.ticker = ticker.upper()
        self.shares = shares
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.current_price = 0
        self.unrealized_pnl = 0
        self.unrealized_pnl_pct = 0

class Portfolio:
    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.cash = 100000  # Start with $100k
        self.total_value = self.cash
        
    def add_position(self, ticker: str, shares: float, price: float, date_str: str = None) -> Dict:
        """Add or update a position"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        cost = shares * price
        if cost > self.cash:
            return {"error": f"Insufficient cash. Need ${cost:.2f}, have ${self.cash:.2f}"}
        
        ticker = ticker.upper()
        if ticker in self.positions:
            # Update existing position (average cost)
            existing = self.positions[ticker]
            total_shares = existing.shares + shares
            total_cost = (existing.shares * existing.entry_price) + cost
            avg_price = total_cost / total_shares
            
            existing.shares = total_shares
            existing.entry_price = avg_price
        else:
            self.positions[ticker] = Position(ticker, shares, price, date_str)
        
        self.cash -= cost
        return {"success": f"Added {shares} shares of {ticker} at ${price:.2f}"}
    
    def remove_position(self, ticker: str, shares: float = None) -> Dict:
        """Remove all or partial position"""
        ticker = ticker.upper()
        if ticker not in self.positions:
            return {"error": f"No position in {ticker}"}
        
        position = self.positions[ticker]
        current_price = get_last_price_from_history(ticker) or position.entry_price
        
        if shares is None or shares >= position.shares:
            # Sell entire position
            proceeds = position.shares * current_price
            self.cash += proceeds
            pnl = (current_price - position.entry_price) * position.shares
            del self.positions[ticker]
            return {"success": f"Sold all {position.shares} shares of {ticker} for ${proceeds:.2f}, PnL: ${pnl:.2f}"}
        else:
            # Partial sell
            proceeds = shares * current_price
            self.cash += proceeds
            pnl = (current_price - position.entry_price) * shares
            position.shares -= shares
            return {"success": f"Sold {shares} shares of {ticker} for ${proceeds:.2f}, PnL: ${pnl:.2f}"}
    
    def update_positions(self) -> None:
        """Update current prices and PnL for all positions"""
        for ticker, position in self.positions.items():
            current_price = get_last_price_from_history(ticker)
            if current_price:
                position.current_price = current_price
                position.unrealized_pnl = (current_price - position.entry_price) * position.shares
                position.unrealized_pnl_pct = ((current_price - position.entry_price) / position.entry_price) * 100
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary with current values"""
        self.update_positions()
        
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_position_value = sum(pos.current_price * pos.shares for pos in self.positions.values())
        self.total_value = self.cash + total_position_value
        
        positions_data = []
        for ticker, pos in self.positions.items():
            # Get technical signal for each position
            try:
                tech = get_technical_signals(ticker, period="1mo")
                signal = tech.get("overall_signal", "HOLD") if "error" not in tech else "HOLD"
            except:
                signal = "HOLD"
            
            positions_data.append({
                "ticker": ticker,
                "shares": pos.shares,
                "entry_price": pos.entry_price,
                "current_price": pos.current_price,
                "market_value": pos.current_price * pos.shares,
                "unrealized_pnl": pos.unrealized_pnl,
                "unrealized_pnl_pct": pos.unrealized_pnl_pct,
                "entry_date": pos.entry_date,
                "signal": signal
            })
        
        return {
            "cash": self.cash,
            "total_position_value": total_position_value,
            "total_portfolio_value": self.total_value,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_unrealized_pnl_pct": (total_unrealized_pnl / (self.total_value - total_unrealized_pnl)) * 100 if self.total_value != total_unrealized_pnl else 0,
            "positions": positions_data,
            "position_count": len(self.positions)
        }

# Global portfolio instance (in production, this would be user-specific)
_portfolio = Portfolio()

def get_portfolio() -> Portfolio:
    return _portfolio

def add_position(ticker: str, shares: float, price: float = None) -> Dict:
    """Add position to portfolio"""
    if price is None:
        price = get_last_price_from_history(ticker)
        if not price:
            return {"error": f"Could not get current price for {ticker}"}
    
    return _portfolio.add_position(ticker, shares, price)

def remove_position(ticker: str, shares: float = None) -> Dict:
    """Remove position from portfolio"""
    return _portfolio.remove_position(ticker, shares)

def get_portfolio_summary() -> Dict:
    """Get current portfolio summary"""
    return _portfolio.get_portfolio_summary()
