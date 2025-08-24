from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from typing import List

from .models import TickerProfile, EarningsEvent, ReactionResponse, NewsItem
from .services.fundamentals import build_profile
from .services.earnings import get_earnings_events, earnings_reaction
from .sources.news_rss import fetch_headlines

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
    
# in main.py
@app.get("/debug/{ticker}")
async def debug_sources(ticker: str):
    from .sources.prices_yfinance import get_last_price_from_history, get_info
    from datetime import datetime
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
