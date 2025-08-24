# Stock Analyst (Personal)

Two pillars:
1. **Company Research Card** (profile, valuation snapshot, factor hints)
2. **Earnings Reaction Analyzer** (how the stock reacts to earnings: 1d/5d returns vs surprises)

> Personal research tool. Not investment advice.

---

## Quickstart (with `uv`)

```bash
# 1) Clone or unzip this repo
cd stock-analyst

# 2) Create env & install deps
uv venv
uv sync

# 3) Copy env
cp .env.sample .env
# Edit SEC_USER_AGENT with your info (for EDGAR courtesy)

# 4) Start the backend (FastAPI)
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 5) Start the UI (Streamlit)
uv run streamlit run main.py
```

Open Streamlit (it will auto-open) and set the backend URL if needed
(defaults to `http://localhost:8000`).

---

## Structure

```
stock-analyst/
  main.py             # Streamlit UI
  api/                # FastAPI backend (data/web fetch & compute)
  data/               # local caches
  tests/
  README.md
  pyproject.toml
```

---

## Notes on data sources

- **Prices & basic fundamentals:** `yfinance` (free, good enough to start).
- **Earnings history & surprises:** `yfinance.Ticker().get_earnings_dates()` if available.
  Coverage can be patchy; swap in a paid API later if you need higher fidelity.
- **News RSS:** Yahoo Finance RSS (best-effort). Some headlines or transcripts can be paywalled.

---

## Roadmap (suggested)
- Add peer comparison & factor scores.
- Add caching TTLs & daily refresh jobs.
- Add backtests on earnings drift / post-earnings momentum.
- Optional: switch to paid APIs for reliable consensus estimates.
