from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import numpy as np

from .earnings import get_earnings_events, earnings_reaction
from .technical import get_technical_signals
from .trading import get_surprise_signal
from ..sources.prices_yfinance import get_price_history

def backtest_earnings_strategy(ticker: str, strategy: str = "surprise", lookback_days: int = 365) -> Dict:
    """Backtest earnings-based trading strategies"""
    try:
        events = get_earnings_events(ticker, limit=20)
        if not events:
            return {"error": "No earnings events found"}
        
        # Get price data
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        prices = get_price_history(ticker, start=start_date)
        
        if prices.empty:
            return {"error": "No price data"}
        
        # Handle MultiIndex columns
        if isinstance(prices.columns, pd.MultiIndex):
            prices.columns = prices.columns.droplevel(1)
        
        trades = []
        total_return = 0
        win_count = 0
        
        for event in events:
            if not event.report_date:
                continue
                
            # Find entry price (day before earnings)
            entry_date = pd.to_datetime(event.report_date) - timedelta(days=1)
            exit_date = pd.to_datetime(event.report_date) + timedelta(days=1)
            
            try:
                entry_price = float(prices.loc[prices.index <= entry_date, 'Close'].iloc[-1])
                exit_price = float(prices.loc[prices.index >= exit_date, 'Close'].iloc[0])
            except (IndexError, KeyError):
                continue
            
            # Generate signal based on strategy
            if strategy == "surprise":
                signal = get_surprise_signal(event)
                position = 1 if signal in ["STRONG_BUY", "WEAK_BUY"] else -1 if signal == "SELL" else 0
            elif strategy == "always_long":
                position = 1
            elif strategy == "volatility":
                # Long if high expected volatility
                position = 1 if abs(event.eps_surprise_pct or 0) > 2 else 0
            else:
                position = 0
            
            if position != 0:
                pnl = position * ((exit_price - entry_price) / entry_price) * 100
                total_return += pnl
                if pnl > 0:
                    win_count += 1
                
                trades.append({
                    "date": event.report_date,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "position": position,
                    "pnl_pct": pnl,
                    "signal": signal if strategy == "surprise" else strategy
                })
        
        if not trades:
            return {"error": "No valid trades found"}
        
        return {
            "ticker": ticker.upper(),
            "strategy": strategy,
            "total_trades": len(trades),
            "win_rate": win_count / len(trades),
            "total_return_pct": total_return,
            "avg_return_pct": total_return / len(trades),
            "best_trade_pct": max(t["pnl_pct"] for t in trades),
            "worst_trade_pct": min(t["pnl_pct"] for t in trades),
            "trades": trades[-10:]  # Last 10 trades
        }
        
    except Exception as e:
        return {"error": str(e)}

def backtest_technical_strategy(ticker: str, strategy: str = "rsi_oversold", lookback_days: int = 180) -> Dict:
    """Backtest technical analysis strategies"""
    try:
        # Get price data
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        prices = get_price_history(ticker, start=start_date)
        
        if prices.empty:
            return {"error": "No price data"}
        
        # Handle MultiIndex columns
        if isinstance(prices.columns, pd.MultiIndex):
            prices.columns = prices.columns.droplevel(1)
        
        # Calculate technical indicators
        close = prices['Close']
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Moving averages
        ma_20 = close.rolling(20).mean()
        ma_50 = close.rolling(50).mean()
        
        trades = []
        position = 0
        entry_price = 0
        
        for i in range(50, len(prices)):  # Start after indicators are calculated
            current_price = float(close.iloc[i])
            current_rsi = float(rsi.iloc[i])
            current_ma20 = float(ma_20.iloc[i])
            current_ma50 = float(ma_50.iloc[i])
            
            # Entry signals
            if position == 0:
                if strategy == "rsi_oversold" and current_rsi < 30:
                    position = 1
                    entry_price = current_price
                elif strategy == "ma_crossover" and current_ma20 > current_ma50 and ma_20.iloc[i-1] <= ma_50.iloc[i-1]:
                    position = 1
                    entry_price = current_price
            
            # Exit signals (after 5 days or stop loss)
            elif position == 1:
                days_held = 5  # Simple 5-day hold
                if i >= len(prices) - 1 or (current_price / entry_price - 1) < -0.05:  # 5% stop loss
                    pnl = ((current_price - entry_price) / entry_price) * 100
                    trades.append({
                        "entry_date": prices.index[i-days_held].strftime("%Y-%m-%d"),
                        "exit_date": prices.index[i].strftime("%Y-%m-%d"),
                        "entry_price": entry_price,
                        "exit_price": current_price,
                        "pnl_pct": pnl
                    })
                    position = 0
        
        if not trades:
            return {"error": "No trades generated"}
        
        total_return = sum(t["pnl_pct"] for t in trades)
        win_count = sum(1 for t in trades if t["pnl_pct"] > 0)
        
        return {
            "ticker": ticker.upper(),
            "strategy": strategy,
            "total_trades": len(trades),
            "win_rate": win_count / len(trades),
            "total_return_pct": total_return,
            "avg_return_pct": total_return / len(trades),
            "best_trade_pct": max(t["pnl_pct"] for t in trades),
            "worst_trade_pct": min(t["pnl_pct"] for t in trades),
            "trades": trades[-5:]  # Last 5 trades
        }
        
    except Exception as e:
        return {"error": str(e)}
