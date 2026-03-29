import yfinance as yf
import streamlit as st
import pandas as pd
from datetime import datetime
from email.mime.text import MIMEText
import smtplib
import requests

# ==============================================================================
# SECURE CONFIGURATION (ACCESSING STREAMLIT SECRETS)
# ==============================================================================
try:
    EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    EMAIL_RECEIVER = st.secrets["EMAIL_RECEIVER"]
except:
    st.error("Please configure EMAIL_SENDER, EMAIL_PASSWORD, and EMAIL_RECEIVER in Streamlit Cloud Secrets.")
    st.stop()

# ==============================================================================
# DATA FETCHING MODULE
# ==============================================================================
@st.cache_data(ttl=3600)  # Cache data for one hour
def get_market_metrics():
    """Fetch all necessary market data for signals."""
    metrics = {}
    try:
        # 1. ENB.TO Data
        enb = yf.Ticker("ENB.TO")
        metrics['enb_price'] = enb.history(period="1d")["Close"].iloc[-1]
        metrics['enb_div'] = enb.dividends.last("365D").sum()
        
        # 2. Tech Drawdown Data
        nasdaq = yf.Ticker("^IXIC")
        nas_hist = nasdaq.history(period="6mo")
        peak = nas_hist["Close"].max()
        metrics['nasdaq_drawdown'] = (nas_hist["Close"].iloc[-1] - peak) / peak * 100
        
        # 3. Dividend Comparison Tickers
        metrics['ry_yield'] = yf.Ticker("RY.TO").info.get('trailingAnnualDividendYield', 0) * 100
        metrics['td_yield'] = yf.Ticker("TD.TO").info.get('trailingAnnualDividendYield', 0) * 100
        metrics['fts_yield'] = yf.Ticker("FTS.TO").info.get('trailingAnnualDividendYield', 0) * 100

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        st.stop()
        
    return metrics

def calculate_portfolio():
    """Calculates portfolio value based on static allocation (can be upgraded later to track real lots)."""
    # GIC Income Estimates
    monthly_gic_amount = 300000
    compound_gic_amount = 200000
    avg_rate = 0.036
    
    gic_monthly_est_income = (monthly_gic_amount * avg_rate) / 12
    gic_total_value = monthly_gic_amount + compound_gic_amount
    
    # Stock Value Estimates (Initially use allocation until positions are bought)
    stock_value = 500000 # ENB (225k) + Tech (275k) allocated
    
    total_value = gic_total_value + stock_value
    return gic_total_value, gic_monthly_est_income, total_value

# ==============================================================================
# SIGNAL MODULES (LOGIC & UI STYLING)
# ==============================================================================
def apply_enb_style(label, is_current):
    """Applies green border styling to the current ENB zone."""
    if is_current:
        return f"""
        <div style="border: 2px solid #28a745; border-radius: 8px; padding: 10px; background-color: #f8fff9;">
            <b style="color: #28a745;">Current Zone</b><br>
            <b>{label}</b>
        </div>
        """
    else:
        return f"""
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 10px; background-color: #fff;">
            <b>{label}</b>
        </div>
        """

def show_enb_signals(metrics, return_signals=False):
    """Render ENB signal UI (modelled on the provided image)."""
    price = metrics['enb_price']
    dividend = metrics['enb_div']
    yld = (dividend / price) * 100

    # Determine signal
    signal = "HOLD (Yield Low)"
    if 5.2 <= yld < 5.8:
        signal = "SMALL BUY"
    elif 5.8 <= yld < 6.5:
        signal = "BUY MEDIUM"
    elif 6.5 <= yld < 7.0:
        signal = "STRONG BUY"
    elif yld >= 7.0:
        signal = "STRONG BUY ALL"

    if return_signals:
        return yld, signal

    st.subheader("ENB yield entry zones")
    st.write("Buy based on yield, not price — higher yield = better entry")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        is_current = 5.2 <= yld < 5.8
        st.markdown(apply_enb_style("Zone 1 — Fair value", is_current), unsafe_allow_html=True)
        st.write("Price: $70–73\nYield: 5.2–5.5%")
        st.info("→ Small buy $10–20K")

    with col2:
        is_current = 5.8 <= yld < 6.5
        st.markdown(apply_enb_style("Zone 2 — Good value", is_current), unsafe_allow_html=True)
        st.write("Price: $65–68\nYield: 5.8–6.2%")
        st.warning("→ Buy $25–40K")

    with col3:
        is_current = 6.5 <= yld < 7.0
        st.markdown(apply_enb_style("Zone 3 — Strong buy", is_current), unsafe_allow_html=True)
        st.write("Price: $60–63\nYield: 6.5–7%")
        st.error("→ Buy $40–60K")

    with col4:
        is_current = yld >= 7.0
        st.markdown(apply_enb_style("Zone 4 — All-in deploy", is_current), unsafe_allow_html=True)
        st.write("Price: < $58\nYield: > 7%")
        st.error("→ Deploy all remaining")

    # Summary Line
    color = "green" if "BUY" in signal else "black"
    st.markdown(f"--- \n#### ENB: **${price:.2f}** · Dividend: **${dividend:.2f}/yr** · Yield: <span style='color:green;'>{yld:.2f}%</span> · Signal: <span style='color:{color};'>{signal}</span>", unsafe_allow_html=True)

def get_live_gic_rates():
    try:
        # Fetching from a reliable Canadian rate aggregator
        url = "https://wowa.ca/gic-rates"
        header = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=header)
        
        # Scrape all tables on the page
        tables = pd.read_html(response.text)
        
        # Table 0 is usually the "Best Rates" summary
        df = tables[0] 
        
        # Clean the data: Keep columns for Term and Rate
        # Based on WOWA's structure: [Provider, 1-Year, 2-Year, 3-Year, 4-Year, 5-Year]
        best_rates = {
            "1 Year": df.iloc[0, 1], # Top provider for 1 Year
            "2 Year": df.iloc[0, 6], # Adjust indices based on live table structure
            "3 Year": df.iloc[0, 7],
            "5 Year": df.iloc[0, 9]
        }
        return best_rates, df.head(10)
    except Exception as e:
        # Fallback rates if the scraper fails
        return {"1 Year": "3.65%", "2 Year": "3.54%", "3 Year": "3.72%", "5 Year": "3.85%"}, None
    
def show_tech_signals(drawdown, return_signals=False):
    """Render Nasdaq drawdown signals (modelled on the provided image)."""
    # Signal Logic
    if drawdown >= -5:
        current_idx, action_signal = 0, "HOLD"
    elif -10 <= drawdown < -5:
        current_idx, action_signal = 1, "BUY SMALL"
    elif -15 <= drawdown < -10:
        current_idx, action_signal = 2, "BUY MEDIUM"
    elif -20 <= drawdown < -15:
        current_idx, action_signal = 3, "BUY LARGE"
    else:
        current_idx, action_signal = 4, "BUY ALL IN"

    if return_signals:
        return drawdown, action_signal

    st.subheader("Nasdaq drawdown → tech buy signal")
    
    cols = st.columns(5)
    labels = ["0 to -5%", "-5%", "-10%", "-15%", "-20%+"]
    actions = ["Hold tech", "Buy 20%", "Buy 30%", "Buy 30%", "All in"]

    for i, col in enumerate(cols):
        with col:
            bg_color = "#f8fff9" if i == current_idx else "#fff"
            border_color = "#28a745" if i == current_idx else "#ddd"
            
            st.markdown(f"""
            <div style="border: 2px solid {border_color}; border-radius: 8px; padding: 10px; background-color: {bg_color}; text-align: center;">
                <b>{labels[i]}</b><br>
                {actions[i]}
            </div>
            """, unsafe_allow_html=True)
            
    color = "green" if "BUY" in action_signal else "black"
    st.markdown(f"--- \n#### Nasdaq Drawdown: <span style='color:red;'>{drawdown:.2f}%</span> · Tech Signal: <span style='color:{color};'>{action_signal} TECH</span>", unsafe_allow_html=True)

# ==============================================================================
# UI MAIN APPLICATION
# ==============================================================================
st.set_page_config(page_title="Investment Dashboard", layout="wide")
st.title("📊 WealthEngine™ $1M Portfolio Dashboard")

# Initialize and cache market data
metrics = get_market_metrics()
gic_value, gic_income, total_value = calculate_portfolio()

# Define multi-tab layout exactly as requested
tabs = st.tabs(["Overview", "Portfolio", "Signals", "GIC", "Tax optimization", "Action plan"])

# ------------------------------------------------------------------------------
# TABS CONTENT
# ------------------------------------------------------------------------------
with tabs[0]: # Overview
    st.header("Strategic Allocation")
    st.metric("Total Planned Capital", f"${total_value/1e6:.1f}M")
    st.write(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M Toronto')}")
    st.line_chart(pd.DataFrame({'ENB Price (6M)': yf.Ticker("ENB.TO").history(period="6mo")['Close']}))

with tabs[1]: # Portfolio (Accounting)
    st.header("Asset Balance")
    col1, col2, col3 = st.columns(3)
    col1.metric("GICs (Planned)", f"${gic_value:,}")
    col2.metric("Income Generated/mo", f"${gic_income:,.2f}")
    col3.metric("Stock Allocation (Un-deployed)", f"${500000:,}")
    st.info("Planned Allocation: 50% GIC | 22.5% ENB | 27.5% U.S. Tech")

with tabs[2]: # Signals (Modelled on Image)
    show_enb_signals(metrics)
    st.write("")
    show_tech_signals(metrics['nasdaq_drawdown'])

with tabs[3]:
    st.header("GIC Strategy & Real-Time Rates")
    
    # 1. Fetch live data
    rates, full_table = get_live_gic_rates()
    
    # 2. Clean numeric values for calculations
    rate_2y = float(rates["2 Year"].replace('%', '')) / 100
    rate_3y = float(rates["3 Year"].replace('%', '')) / 100

    col_left, col_right = st.columns(2)
    
    with col_left:
        principal_payout = 300000
        monthly_income = (principal_payout * rate_2y) / 12
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 20px; background-color: #ffffff;">
            <h4 style="margin-top:0;">Monthly Payout Engine</h4>
            <table style="width:100%">
                <tr><td>Principal</td><td style="text-align:right"><b>${principal_payout:,}</b></td></tr>
                <tr><td>Live 2Y Rate</td><td style="text-align:right; color:green;"><b>{rates['2 Year']}</b></td></tr>
                <tr><td>Monthly income</td><td style="text-align:right; color:#1f77b4;"><b>${monthly_income:,.2f}</b></td></tr>
                <tr><td>Annual income</td><td style="text-align:right"><b>${monthly_income * 12:,.2f}</b></td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        principal_core = 200000
        y1 = principal_core * (1 + rate_3y)
        y3 = principal_core * (1 + rate_3y)**3
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 20px; background-color: #ffffff;">
            <h4 style="margin-top:0;">Compound Core</h4>
            <table style="width:100%">
                <tr><td>Principal</td><td style="text-align:right"><b>${principal_core:,}</b></td></tr>
                <tr><td>Live 3Y Rate</td><td style="text-align:right; color:green;"><b>{rates['3 Year']}</b></td></tr>
                <tr><td>Year 1 value</td><td style="text-align:right; color:#1f77b4;"><b>${y1:,.2f}</b></td></tr>
                <tr><td>Year 3 value</td><td style="text-align:right; color:#1f77b4;"><b>${y3:,.2f}</b></td></tr>
                <tr><td>Total Gain</td><td style="text-align:right; color:green;"><b>${y3 - principal_core:,.2f}</b></td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    st.write("### Live Market Comparison")
    if full_table is not None:
        st.dataframe(full_table, use_container_width=True)
    else:
        st.warning("Could not load live table. Using cached rate estimates.")

# with tabs[3]: # GIC (Ladder Strategy)
#     st.header("GIC Income Engine")
#     st.warning("Strategy: 2–3–5 Year Ladder using monthly payout vs compound.")
#     st.write(f"Estimated monthly flow: ${gic_income:,.2f}")
#     st.caption("TD PAC/CDA TR/TD BK instruments assumed. CDIC limits of $100K/issuer apply.")

with tabs[4]: # Tax Optimization (Canadian Context)
    st.header("Canadian Account Placement Strategy")
    st.write("Ensure asset placement maximizes after-tax returns.")
    
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.subheader("TFSA (Tax-Free Growth)")
        st.success("- Canadian High-Yield Stocks (ENB, Banks)\n- Growth Stocks (US Tech/AI - *accept 15% US withholding*)")
        st.subheader("RRSP (Tax-Deferral)")
        st.info("- U.S. Tech (MSFT, NVDA) -> **Zero WHT on dividends.**\n- High-Yield bonds or GICs")

with tabs[5]: # Action Plan (Execution Playbook)
    st.header("Execution Rules")
    st.markdown("""
    1.  **Weekly Check:** Run this dashboard every Monday.
    2.  **Trigger Rules:** Deploy capital *only* when Signals tab shows 'BUY' (as defined in Zone System).
    3.  **Liquidity Flow:** Reinvest GIC monthly income into 1-year terms (annually paid) OR deploy into dividend stocks when they hit high-yield zones.
    """)

# ==============================================================================
# EMAIL ALERT FUNCTION
# ==============================================================================
def send_email_alert(enb_p, enb_y, enb_a, nas_d, tech_a):
    """Securely sends a daily summary via email."""
    report_text = f"""
$1M Investment Signal Alert

{datetime.now().strftime('%Y-%m-%d Toronto')}

[ENB SIGNALS]
Price: {enb_p:.2f}
Yield: {enb_y:.2f}%
Action: {enb_a}

[TECH SIGNALS]
Nasdaq Drawdown: {nas_d:.2f}%
Action: {tech_a} TECH

Full dashboard available at Streamlit Cloud URL.
"""
    msg = MIMEText(report_text)
    msg["Subject"] = f"Action Alert: {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        st.success("Dispatched alert email.")
    except Exception as e:
        st.error(f"Failed to send email. Check credentials: {e}")

# Sidebar Button for Manual Email Dispatched
if st.sidebar.button("📧 Dispatched Daily Alert Manual"):
    # Re-calculate signals for the email body
    yld, enb_action = show_enb_signals(metrics, return_signals=True)
    drawdown, tech_action = show_tech_signals(metrics['nasdaq_drawdown'], return_signals=True)
    send_email_alert(metrics['enb_price'], yld, enb_action, drawdown, tech_action)