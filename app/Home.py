import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Stock Analyst", layout="wide")

st.title("📈 Stock Analyst — Personal")
backend_default = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
backend_url = st.sidebar.text_input("Backend URL", backend_default)

ticker = st.text_input("Ticker", "AAPL").strip().upper()
if not ticker:
    st.stop()

def get_json(path: str):
    url = f"{backend_url}{path}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

tab1, tab2, tab3 = st.tabs(["Company Card", "Earnings Analyzer", "News"])

with tab1:
    try:
        prof = get_json(f"/profile/{ticker}")
    except Exception as e:
        st.error(f"Failed to load profile: {e}")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price", f"{prof.get('price', '—')}")
    c2.metric("Market Cap", f"{prof.get('market_cap', '—')}")
    c3.metric("P/E", f"{round(prof['pe'], 2) if prof.get('pe') else '—'}")
    c4.metric("P/FCF", f"{round(prof['pfcf'], 2) if prof.get('pfcf') else '—'}")

    c5, c6, c7 = st.columns(3)
    c5.metric("EV/EBITDA", f"{round(prof['ev_ebitda'], 2) if prof.get('ev_ebitda') else '—'}")
    c6.metric("Gross Margin", f"{round(100*prof['gross_margin'],1)}%" if prof.get("gross_margin") else "—")
    c7.metric("Profit Margin", f"{round(100*prof['profit_margin'],1)}%" if prof.get("profit_margin") else "—")

    st.subheader(prof.get("name") or ticker)
    st.caption(f"{prof.get('sector', '—')} | {prof.get('industry', '—')}")
    if prof.get("description"):
        st.write(prof["description"])

with tab2:
    left, right = st.columns([2,1])
    try:
        events = get_json(f"/earnings/{ticker}")
        reaction = get_json(f"/reaction/{ticker}")
    except Exception as e:
        st.error(f"Failed to load earnings data: {e}")
        st.stop()

    ev_df = pd.DataFrame(events)
    if not ev_df.empty:
        ev_df_display = ev_df.rename(columns={
            "report_date":"Date",
            "eps_actual":"EPS Actual",
            "eps_estimate":"EPS Est",
            "eps_surprise_pct":"EPS Surprise %"
        })
        left.subheader("Earnings History")
        left.dataframe(ev_df_display, use_container_width=True, hide_index=True)
    else:
        left.info("No earnings events found.")

    right.subheader("Reaction Summary")
    summary = reaction.get("summary", {}) if reaction else {}
    colA, colB = right.columns(2)
    colA.metric("Avg Upside (1d)", f"{summary.get('average_upside_pct') and round(summary['average_upside_pct'],2)}%")
    colB.metric("Avg Downside (1d)", f"{summary.get('average_downside_pct') and round(summary['average_downside_pct'],2)}%")
    right.metric("Avg Abs Move (1d)", f"{summary.get('average_abs_move_pct') and round(summary['average_abs_move_pct'],2)}%")
    colC, colD = right.columns(2)
    colC.metric("Beats (EPS)", f"{summary.get('beats_count') or '—'}")
    colD.metric("Misses (EPS)", f"{summary.get('misses_count') or '—'}")

    items = pd.DataFrame(reaction.get("items", []))
    if not items.empty and "report_date" in items:
        items["report_date"] = pd.to_datetime(items["report_date"])
        chart_df = items[["report_date", "next_day_return_pct", "five_day_return_pct"]].melt(
            id_vars="report_date", var_name="window", value_name="return_pct"
        )
        chart_df["window"] = chart_df["window"].map({
            "next_day_return_pct": "Next Day",
            "five_day_return_pct": "5 Day"
        })
        fig = px.bar(chart_df, x="report_date", y="return_pct", color="window", barmode="group",
                     title="Earnings Reaction Returns")
        fig.update_layout(xaxis_title="Report Date", yaxis_title="Return %")
        left.plotly_chart(fig, use_container_width=True)

with tab3:
    try:
        news = get_json(f"/news/{ticker}")
    except Exception as e:
        st.error(f"Failed to load news: {e}")
        st.stop()

    if not news:
        st.info("No recent headlines found.")
    else:
        for n in news:
            st.write(f"**{n.get('title','(no title)')}**")
            meta = []
            if n.get("source"): meta.append(n["source"])
            if n.get("published"): meta.append(n["published"])
            if meta: st.caption(" • ".join(meta))
            st.write(f"[Read more]({n.get('link')})")
            if n.get("summary"):
                with st.expander("Summary"):
                    st.write(n["summary"])
            st.markdown("---")
