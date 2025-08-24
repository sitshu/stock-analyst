from __future__ import annotations
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from typing import List

from .models import TickerProfile, EarningsEvent, ReactionResponse, NewsItem
from .services.fundamentals import build_profile
from .services.earnings import get_earnings_events, earnings_reaction
from .sources.news_rss import fetch_headlines
from .util.http import reset_session as reset_http_session
from .services.trading import get_earnings_risk_metrics, export_trading_data, check_trading_alerts
from .services.technical import get_comprehensive_technical_analysis, get_multi_timeframe_signals
from .services.backtesting import backtest_earnings_strategy, backtest_technical_strategy
from .services.portfolio import add_position, remove_position, get_portfolio_summary
from .services.calendar import get_earnings_calendar, get_sector_comparison, get_high_volatility_calendar

class Settings(BaseSettings):
    cors_allow_origins: List[str] = ["*"]  # personal use; tighten later
    class Config:
        env_prefix = ""

settings = Settings()

app = FastAPI(title="Stock Analyst API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/profile/{ticker}", response_model=TickerProfile)
async def profile(ticker: str):
    try:
        return build_profile(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/earnings/{ticker}", response_model=List[EarningsEvent])
async def earnings(ticker: str):
    try:
        return get_earnings_events(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reaction/{ticker}", response_model=ReactionResponse)
async def reaction(ticker: str):
    try:
        return earnings_reaction(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/news/{ticker}", response_model=List[NewsItem])
async def news(ticker: str):
    try:
        return fetch_headlines(ticker, limit=20)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/calendar/earnings")
async def earnings_calendar(days_ahead: int = 14, tickers: str = None):
    """Get upcoming earnings calendar"""
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(",")] if tickers else None
        return get_earnings_calendar(days_ahead, ticker_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/calendar/high-volatility")
async def high_volatility_calendar(min_avg_move: float = 5.0, days_ahead: int = 14):
    """Get high volatility earnings calendar"""
    try:
        return get_high_volatility_calendar(min_avg_move, days_ahead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sector/comparison/{ticker}")
async def sector_comparison(ticker: str, peers: str = None):
    """Get sector peer comparison"""
    try:
        peer_list = [t.strip().upper() for t in peers.split(",")] if peers else None
        return get_sector_comparison(ticker, peer_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/backtest/earnings/{ticker}")
async def backtest_earnings(ticker: str, strategy: str = "surprise", lookback_days: int = 365):
    """Backtest earnings strategy"""
    try:
        return backtest_earnings_strategy(ticker, strategy, lookback_days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/backtest/technical/{ticker}")
async def backtest_technical(ticker: str, strategy: str = "rsi_oversold", lookback_days: int = 180):
    """Backtest technical strategy"""
    try:
        return backtest_technical_strategy(ticker, strategy, lookback_days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio")
async def portfolio_summary():
    """Get portfolio summary"""
    try:
        return get_portfolio_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/portfolio/add")
async def add_portfolio_position(ticker: str, shares: float, price: float = None):
    """Add position to portfolio"""
    try:
        return add_position(ticker, shares, price)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/portfolio/remove")
async def remove_portfolio_position(ticker: str, shares: float = None):
    """Remove position from portfolio"""
    try:
        return remove_position(ticker, shares)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/technical/{ticker}")
async def technical_analysis(ticker: str):
    """Get technical analysis signals"""
    try:
        return get_comprehensive_technical_analysis(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/technical/multi-timeframe/{ticker}")
async def multi_timeframe_signals(ticker: str):
    """Get signals across multiple timeframes"""
    try:
        return get_multi_timeframe_signals(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trading/risk-metrics/{ticker}")
async def risk_metrics(ticker: str):
    """Get earnings risk metrics for position sizing"""
    try:
        return get_earnings_risk_metrics(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trading/export")
async def export_data(tickers: str):
    """Export trading data for multiple tickers (comma-separated)"""
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        df = export_trading_data(ticker_list)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trading/alerts")
async def trading_alerts(watchlist: str):
    """Check trading alerts for watchlist (comma-separated tickers)"""
    try:
        ticker_list = [t.strip().upper() for t in watchlist.split(",")]
        return check_trading_alerts(ticker_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/reset-session")
async def reset_session():
    """Reset HTTP session (useful when changing TLS impersonation settings)"""
    reset_http_session()
    prices_yfinance._session = None  # Reset yfinance session too
    return {"status": "session reset"}


@app.get("/debug/{ticker}")
async def debug_sources(ticker: str):
    from .sources.prices_yfinance import get_last_price_from_history, get_info
    last_close = get_last_price_from_history(ticker)
    info = get_info(ticker)   # try fundamentals; empty dict if still blocked
    return {
        "symbol": ticker.upper(),
        "last_close": last_close,
        "has_info": bool(info),
        "ebitda": info.get("ebitda"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "yf.download + TLS impersonation for info",
    }
