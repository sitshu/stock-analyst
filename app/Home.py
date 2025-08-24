import streamlit as st
import requests

st.set_page_config(page_title="Stock Analyst", layout="wide")
st.title("Stock Analyst")

backend_url = st.sidebar.text_input("Backend URL", "http://localhost:8000")
ticker = st.text_input("Ticker", "AAPL")

if st.button("Check health"):
    try:
        r = requests.get(f"{backend_url}/health")
        st.write(r.json())
    except Exception as e:
        st.error(str(e))
