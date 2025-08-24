from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

class TickerProfile(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    price: Optional[float] = None
    pe: Optional[float] = None
    pfcf: Optional[float] = None
    ev_ebitda: Optional[float] = None
    gross_margin: Optional[float] = None
    profit_margin: Optional[float] = None
    description: Optional[str] = None

class EarningsEvent(BaseModel):
    fiscal_quarter: Optional[str] = None
    report_date: date
    eps_actual: Optional[float] = None
    eps_estimate: Optional[float] = None
    eps_surprise_pct: Optional[float] = None
    revenue_actual: Optional[float] = None
    revenue_estimate: Optional[float] = None
    revenue_surprise_pct: Optional[float] = None

class ReactionItem(BaseModel):
    report_date: date
    next_day_return_pct: Optional[float] = None
    five_day_return_pct: Optional[float] = None
    baseline_volatility_pct: Optional[float] = None  # approx: daily std*sqrt(252)

class ReactionSummary(BaseModel):
    average_upside_pct: Optional[float] = None
    average_downside_pct: Optional[float] = None
    average_abs_move_pct: Optional[float] = None
    beats_count: Optional[int] = None
    misses_count: Optional[int] = None

class ReactionResponse(BaseModel):
    ticker: str
    items: List[ReactionItem] = Field(default_factory=list)
    summary: ReactionSummary

class NewsItem(BaseModel):
    title: str
    link: str
    published: Optional[datetime] = None
    source: Optional[str] = None
    summary: Optional[str] = None
