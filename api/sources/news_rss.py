from __future__ import annotations
from typing import List, Dict
import feedparser
from datetime import datetime, timezone

def yahoo_finance_rss_url(ticker: str) -> str:
    return f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"

def fetch_headlines(ticker: str, limit: int = 20) -> List[Dict]:
    url = yahoo_finance_rss_url(ticker)
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:limit]:
        published = None
        if getattr(entry, "published_parsed", None):
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        items.append({
            "title": entry.get("title"),
            "link": entry.get("link"),
            "published": published.isoformat() if published else None,
            "source": entry.get("source", {}).get("title") if entry.get("source") else "Yahoo Finance",
            "summary": entry.get("summary"),
        })
    return items
