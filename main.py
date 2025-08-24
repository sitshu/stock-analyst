import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px

from api.services.trading import get_surprise_signal

st.set_page_config(page_title="Stock Analyst", layout="wide")

st.title("📈 Stock Analyst — Personal")
backend_default = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
backend_url = st.sidebar.text_input("Backend URL", backend_default)

ticker = st.text_input("Ticker", "AAPL", key="main_ticker").strip().upper()
if not ticker:
    st.stop()

def get_json(path: str):
    url = f"{backend_url}{path}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Company Card", "Technical Analysis", "Earnings Calendar", "Portfolio & Backtesting", "Sector Analysis"])

with tab1:
    try:
        prof = get_json(f"/profile/{ticker}")
    except Exception as e:
        st.error(f"Failed to load profile: {e}")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price", f"${prof.get('price', '—')}")
    c2.metric("Market Cap", f"{prof.get('market_cap', '—')}")
    c3.metric("P/E", f"{round(prof['pe'], 2) if prof.get('pe') else '—'}")
    c4.metric("P/FCF", f"{round(prof['pfcf'], 2) if prof.get('pfcf') else '—'}")

    c5, c6, c7 = st.columns(3)
    c5.metric("EV/EBITDA", f"{round(prof['ev_ebitda'], 2) if prof.get('ev_ebitda') else '—'}")
    c6.metric("Gross Margin", f"{round(100*prof['gross_margin'],1)}%" if prof.get("gross_margin") else "—")
    c7.metric("Profit Margin", f"{round(100*prof['profit_margin'],1)}%" if prof.get("profit_margin") else "—")

    st.subheader(prof.get("name") or ticker)
    st.caption(f"{prof.get('sector', '—')} | {prof.get('industry', '—')}")

with tab2:
    st.subheader("Comprehensive Technical Analysis")
    
    try:
        tech = get_json(f"/technical/{ticker}")
        if "error" in tech:
            st.error(f"Technical analysis error: {tech['error']}")
        else:
            # Price overview
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Current Price", f"${tech['current_price']}")
            col2.metric("1D Change", f"{tech['price_change_1d']:.2f}%", delta=f"{tech['price_change_1d']:.2f}%")
            if tech['price_change_5d']:
                col3.metric("5D Change", f"{tech['price_change_5d']:.2f}%")
            if tech['price_change_20d']:
                col4.metric("20D Change", f"{tech['price_change_20d']:.2f}%")
            
            # Overall signal with strength
            signal_color = {"STRONG_BUY": "🟢", "BUY": "🟢", "HOLD": "🟡", "SELL": "🔴", "STRONG_SELL": "🔴"}
            col5.metric("Signal", f"{signal_color.get(tech['overall_signal'], '⚪')} {tech['overall_signal']}")
            st.caption(f"Strength Score: {tech.get('strength_score', 0)}")
            
            # Technical indicators in tabs
            ind_tab1, ind_tab2, ind_tab3, ind_tab4 = st.tabs(["Moving Averages", "Oscillators", "Bollinger Bands", "Support/Resistance"])
            
            with ind_tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Simple Moving Averages**")
                    st.write(f"MA5: ${tech.get('ma_5', 'N/A')}")
                    st.write(f"MA10: ${tech.get('ma_10', 'N/A')}")
                    st.write(f"MA20: ${tech['ma_20']}")
                    st.write(f"MA50: ${tech['ma_50']}")
                    if tech.get('ma_100'):
                        st.write(f"MA100: ${tech['ma_100']}")
                    if tech.get('ma_200'):
                        st.write(f"MA200: ${tech['ma_200']}")
                
                with col2:
                    st.write("**Exponential Moving Averages**")
                    st.write(f"EMA12: ${tech.get('ema_12', 'N/A')}")
                    st.write(f"EMA26: ${tech.get('ema_26', 'N/A')}")
                    st.write("**Position vs MAs**")
                    st.write(f"vs MA20: {tech.get('price_vs_ma20', 0):.1f}%")
                    st.write(f"vs MA50: {tech.get('price_vs_ma50', 0):.1f}%")
            
            with ind_tab2:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("**RSI (14)**")
                    rsi_color = "🔴" if tech['rsi'] > 70 else "🟢" if tech['rsi'] < 30 else "🟡"
                    st.write(f"{rsi_color} {tech['rsi']:.1f}")
                    if tech['rsi'] > 80:
                        st.caption("Extremely Overbought")
                    elif tech['rsi'] > 70:
                        st.caption("Overbought")
                    elif tech['rsi'] < 20:
                        st.caption("Extremely Oversold")
                    elif tech['rsi'] < 30:
                        st.caption("Oversold")
                
                with col2:
                    st.write("**Stochastic**")
                    st.write(f"K: {tech.get('stoch_k', 'N/A'):.1f}")
                    st.write(f"D: {tech.get('stoch_d', 'N/A'):.1f}")
                    
                    st.write("**Williams %R**")
                    wr = tech.get('williams_r', 0)
                    wr_color = "🟢" if wr < -80 else "🔴" if wr > -20 else "🟡"
                    st.write(f"{wr_color} {wr:.1f}")
                
                with col3:
                    st.write("**MACD**")
                    st.write(f"MACD: {tech['macd']:.4f}")
                    st.write(f"Signal: {tech['macd_signal']:.4f}")
                    st.write(f"Histogram: {tech['macd_histogram']:.4f}")
                    
                    st.write("**CCI (20)**")
                    cci = tech.get('cci', 0)
                    cci_color = "🔴" if cci > 100 else "🟢" if cci < -100 else "🟡"
                    st.write(f"{cci_color} {cci:.1f}")
            
            with ind_tab3:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Bollinger Bands (20,2)**")
                    st.write(f"Upper: ${tech.get('bb_upper', 'N/A')}")
                    st.write(f"Middle: ${tech.get('bb_middle', 'N/A')}")
                    st.write(f"Lower: ${tech.get('bb_lower', 'N/A')}")
                
                with col2:
                    st.write("**BB Analysis**")
                    bb_pos = tech.get('bb_position', 0)
                    if bb_pos > 0.8:
                        st.write("🔴 Near Upper Band")
                    elif bb_pos < 0.2:
                        st.write("🟢 Near Lower Band")
                    else:
                        st.write("🟡 Middle Range")
                    
                    st.write(f"Position: {bb_pos:.1%}")
                    if tech.get('bb_squeeze'):
                        st.write("⚡ Squeeze Detected")
            
            with ind_tab4:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Support & Resistance**")
                    st.write(f"Resistance: ${tech.get('resistance', 'N/A')}")
                    st.write(f"Support: ${tech.get('support', 'N/A')}")
                    
                    # Distance to S&R
                    if tech.get('resistance') and tech.get('support'):
                        res_dist = ((tech['resistance'] - tech['current_price']) / tech['current_price']) * 100
                        sup_dist = ((tech['current_price'] - tech['support']) / tech['current_price']) * 100
                        st.write(f"To Resistance: {res_dist:.1f}%")
                        st.write(f"Above Support: {sup_dist:.1f}%")
                
                with col2:
                    st.write("**Volume Analysis**")
                    vol_color = "🔥" if tech['volume_ratio'] > 2 else "📊"
                    st.write(f"Volume Ratio: {vol_color} {tech['volume_ratio']:.1f}x")
                    st.write(f"Avg Volume (20d): {tech.get('avg_volume_20', 0):,}")
                    
                    st.write("**Volatility**")
                    st.write(f"ATR (14): ${tech.get('atr', 'N/A')}")
            
            # Active signals
            if tech['signals']:
                st.subheader("Active Signals")
                signal_emojis = {
                    "STRONG_UPTREND": "🚀", "UPTREND": "📈", "STRONG_DOWNTREND": "💥", "DOWNTREND": "📉",
                    "EXTREMELY_OVERSOLD": "🟢🟢", "OVERSOLD": "🟢", "EXTREMELY_OVERBOUGHT": "🔴🔴", "OVERBOUGHT": "🔴",
                    "MACD_BULLISH": "📊🟢", "MACD_BEARISH": "📊🔴",
                    "BB_OVERBOUGHT": "📊🔴", "BB_OVERSOLD": "📊🟢", "BB_SQUEEZE": "⚡",
                    "STOCH_OVERSOLD": "🟢", "STOCH_OVERBOUGHT": "🔴",
                    "WILLIAMS_OVERSOLD": "🟢", "WILLIAMS_OVERBOUGHT": "🔴",
                    "CCI_OVERSOLD": "🟢", "CCI_OVERBOUGHT": "🔴",
                    "HIGH_VOLUME": "🔥", "LOW_VOLUME": "📉"
                }
                
                cols = st.columns(3)
                for i, signal in enumerate(tech['signals']):
                    col = cols[i % 3]
                    emoji = signal_emojis.get(signal, "•")
                    col.write(f"{emoji} {signal.replace('_', ' ').title()}")
            
            # Multi-timeframe view
            st.subheader("Multi-Timeframe Analysis")
            try:
                mtf = get_json(f"/technical/multi-timeframe/{ticker}")
                if mtf:
                    tf_col1, tf_col2, tf_col3 = st.columns(3)
                    
                    for i, (timeframe, data) in enumerate(mtf.items()):
                        col = [tf_col1, tf_col2, tf_col3][i]
                        with col:
                            st.write(f"**{timeframe}**")
                            signal_color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
                            trend_color = {"UP": "📈", "DOWN": "📉"}
                            st.write(f"Signal: {signal_color.get(data['signal'], '⚪')} {data['signal']}")
                            st.write(f"Trend: {trend_color.get(data['trend'], '➡️')} {data['trend']}")
                            st.write(f"RSI: {data['rsi']:.1f}")
            except:
                st.info("Multi-timeframe data unavailable")
                
    except Exception as e:
        st.error(f"Failed to load technical analysis: {e}")

with tab3:
    st.subheader("Earnings Calendar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Upcoming Earnings**")
        days_ahead = st.slider("Days ahead", 7, 30, 14)
        watchlist = st.text_input("Custom watchlist (comma-separated)", "AAPL,MSFT,GOOGL,AMZN,TSLA", key="calendar_watchlist")
        
        if st.button("Get Calendar"):
            try:
                calendar = get_json(f"/calendar/earnings?days_ahead={days_ahead}&tickers={watchlist}")
                if calendar:
                    df = pd.DataFrame(calendar)
                    df_display = df.rename(columns={
                        "ticker": "Ticker",
                        "report_date": "Date",
                        "days_until": "Days Until",
                        "eps_estimate": "EPS Est",
                        "avg_move_pct": "Avg Move %",
                        "win_rate": "Win Rate"
                    })
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.info("No upcoming earnings found")
            except Exception as e:
                st.error(f"Calendar error: {e}")
    
    with col2:
        st.write("**High Volatility Earnings**")
        min_move = st.slider("Min avg move %", 3.0, 10.0, 5.0)
        
        try:
            high_vol = get_json(f"/calendar/high-volatility?min_avg_move={min_move}&days_ahead={days_ahead}")
            if high_vol:
                for event in high_vol[:5]:  # Top 5
                    st.write(f"🔥 **{event['ticker']}** - {event['days_until']} days")
                    st.write(f"   Avg move: {event['avg_move_pct']:.1f}% | Win rate: {event['win_rate']*100:.0f}%")
            else:
                st.info("No high volatility earnings found")
        except Exception as e:
            st.error(f"High volatility error: {e}")

with tab4:
    st.subheader("Portfolio & Backtesting")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Portfolio Management**")
        try:
            portfolio = get_json("/portfolio")
            st.metric("Total Value", f"${portfolio['total_portfolio_value']:,.2f}")
            st.metric("Cash", f"${portfolio['cash']:,.2f}")
            st.metric("Unrealized P&L", f"${portfolio['total_unrealized_pnl']:,.2f}", 
                     delta=f"{portfolio['total_unrealized_pnl_pct']:.1f}%")
            
            if portfolio['positions']:
                st.write("**Positions:**")
                pos_df = pd.DataFrame(portfolio['positions'])
                pos_display = pos_df.rename(columns={
                    "ticker": "Ticker",
                    "shares": "Shares", 
                    "current_price": "Price",
                    "market_value": "Value",
                    "unrealized_pnl_pct": "P&L %",
                    "signal": "Signal"
                })
                st.dataframe(pos_display[["Ticker", "Shares", "Price", "Value", "P&L %", "Signal"]], 
                           use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Portfolio error: {e}")
        
        # Add/Remove positions
        st.write("**Trade**")
        action = st.selectbox("Action", ["Buy", "Sell"])
        trade_ticker = st.text_input("Ticker", ticker, key="trade_ticker")
        shares = st.number_input("Shares", min_value=1, value=100)
        
        if action == "Buy" and st.button("Add Position"):
            try:
                result = requests.post(f"{backend_url}/portfolio/add", 
                                     params={"ticker": trade_ticker, "shares": shares})
                if result.status_code == 200:
                    st.success(result.json().get("success", "Position added"))
                else:
                    st.error(result.json().get("detail", "Error adding position"))
            except Exception as e:
                st.error(f"Trade error: {e}")
        
        elif action == "Sell" and st.button("Remove Position"):
            try:
                result = requests.post(f"{backend_url}/portfolio/remove", 
                                     params={"ticker": trade_ticker, "shares": shares})
                if result.status_code == 200:
                    st.success(result.json().get("success", "Position removed"))
                else:
                    st.error(result.json().get("detail", "Error removing position"))
            except Exception as e:
                st.error(f"Trade error: {e}")
    
    with col2:
        st.write("**Backtesting**")
        
        # Earnings strategy backtest
        st.write("*Earnings Strategy*")
        earnings_strategy = st.selectbox("Strategy", ["surprise", "always_long", "volatility"])
        if st.button("Backtest Earnings"):
            try:
                result = get_json(f"/backtest/earnings/{ticker}?strategy={earnings_strategy}")
                if "error" not in result:
                    st.metric("Total Return", f"{result['total_return_pct']:.1f}%")
                    st.metric("Win Rate", f"{result['win_rate']*100:.1f}%")
                    st.metric("Avg Return", f"{result['avg_return_pct']:.1f}%")
                    st.write(f"Trades: {result['total_trades']}")
                else:
                    st.error(result["error"])
            except Exception as e:
                st.error(f"Backtest error: {e}")
        
        # Technical strategy backtest
        st.write("*Technical Strategy*")
        tech_strategy = st.selectbox("Tech Strategy", ["rsi_oversold", "ma_crossover"])
        if st.button("Backtest Technical"):
            try:
                result = get_json(f"/backtest/technical/{ticker}?strategy={tech_strategy}")
                if "error" not in result:
                    st.metric("Total Return", f"{result['total_return_pct']:.1f}%")
                    st.metric("Win Rate", f"{result['win_rate']*100:.1f}%")
                    st.metric("Avg Return", f"{result['avg_return_pct']:.1f}%")
                    st.write(f"Trades: {result['total_trades']}")
                else:
                    st.error(result["error"])
            except Exception as e:
                st.error(f"Backtest error: {e}")

with tab5:
    st.subheader("Sector Analysis")
    
    try:
        comparison = get_json(f"/sector/comparison/{ticker}")
        if "error" not in comparison:
            st.write(f"**{ticker.upper()} vs Sector Peers**")
            
            # Show sector averages
            avg = comparison["sector_averages"]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Sector Avg Move", f"{avg['avg_move_pct']:.1f}%")
            col2.metric("Sector Max Move", f"{avg['max_move_pct']:.1f}%") 
            col3.metric("Sector Win Rate", f"{avg['win_rate']*100:.1f}%")
            col4.metric("Sector Volatility", f"{avg['volatility']:.1f}%")
            
            # Show comparison table
            comp_df = pd.DataFrame(comparison["comparison_data"])
            comp_display = comp_df.rename(columns={
                "ticker": "Ticker",
                "avg_move_pct": "Avg Move %",
                "max_move_pct": "Max Move %",
                "win_rate": "Win Rate %",
                "volatility": "Volatility %",
                "next_earnings": "Next Earnings"
            })
            comp_display["Win Rate %"] = comp_display["Win Rate %"] * 100
            
            # Highlight target ticker
            def highlight_target(row):
                return ['background-color: lightblue' if row.name == 0 else '' for _ in row]
            
            st.dataframe(comp_display.style.apply(highlight_target, axis=1), 
                        use_container_width=True, hide_index=True)
        else:
            st.error(comparison["error"])
    except Exception as e:
        st.error(f"Sector analysis error: {e}")
