import yfinance as yf
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# ================= CONFIG (SECURE) =================
EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
EMAIL_RECEIVER = st.secrets["EMAIL_RECEIVER"]

NASDAQ_TICKER = "^IXIC"
ENB_TICKER = "ENB.TO"

# ================= DATA FUNCTIONS =================

def get_price(ticker):
    data = yf.Ticker(ticker)
    return data.history(period="1d")["Close"].iloc[-1]

def get_dividend(ticker):
    data = yf.Ticker(ticker)
    divs = data.dividends
    if len(divs) == 0:
        return 0
    last_year = divs.last("365D")
    return last_year.sum()

def get_nasdaq_drawdown():
    data = yf.Ticker(NASDAQ_TICKER).history(period="6mo")
    peak = data["Close"].max()
    current = data["Close"].iloc[-1]
    return (current - peak) / peak * 100

# ================= SIGNALS =================

def enb_signal(price, dividend):
    yield_pct = dividend / price * 100

    if yield_pct >= 7:
        action = "STRONG BUY ALL"
    elif yield_pct >= 6.5:
        action = "BUY LARGE"
    elif yield_pct >= 5.8:
        action = "BUY MEDIUM"
    elif yield_pct >= 5.2:
        action = "SMALL BUY"
    else:
        action = "HOLD"

    return yield_pct, action

def tech_signal(drawdown):
    if drawdown <= -20:
        return "BUY ALL TECH"
    elif drawdown <= -15:
        return "BUY LARGE TECH"
    elif drawdown <= -10:
        return "BUY MEDIUM TECH"
    elif drawdown <= -5:
        return "BUY SMALL TECH"
    else:
        return "HOLD TECH"

# ================= EMAIL =================

def send_email_report(enb_price, yield_pct, enb_action, nasdaq_drawdown, tech_action):
    report = f"""
Daily Investment Report - {datetime.now().strftime('%Y-%m-%d')}

ENB Price: {enb_price:.2f}
Yield: {yield_pct:.2f}%
Signal: {enb_action}

Nasdaq Drawdown: {nasdaq_drawdown:.2f}%
Tech Signal: {tech_action}

Action Plan:
- Follow ENB signal
- Follow Tech signal
"""

    msg = MIMEText(report)
    msg["Subject"] = "Daily Investment Signals"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

# ================= STREAMLIT UI =================

st.set_page_config(page_title="Investment Dashboard", layout="wide")

st.title("📊 Investment Dashboard")
st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Fetch data
with st.spinner("Fetching data..."):
    enb_price = get_price(ENB_TICKER)
    enb_dividend = get_dividend(ENB_TICKER)
    nasdaq_drawdown = get_nasdaq_drawdown()

yield_pct, enb_action = enb_signal(enb_price, enb_dividend)
tech_action = tech_signal(nasdaq_drawdown)

# Layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("ENB")
    st.metric("Price", f"${enb_price:.2f}")
    st.metric("Dividend (TTM)", f"${enb_dividend:.2f}")
    st.metric("Yield", f"{yield_pct:.2f}%")
    st.success(f"Action: {enb_action}")

with col2:
    st.subheader("Tech / Nasdaq")
    st.metric("Drawdown", f"{nasdaq_drawdown:.2f}%")
    st.info(f"Action: {tech_action}")

# Email button
if st.button("📧 Send Daily Email"):
    send_email_report(enb_price, yield_pct, enb_action, nasdaq_drawdown, tech_action)
    st.success("Email sent!")

# Chart
st.subheader("ENB Price (6M)")
chart = yf.Ticker(ENB_TICKER).history(period="6mo")
st.line_chart(chart["Close"])
