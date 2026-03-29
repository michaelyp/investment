import yfinance as yf
import smtplib
from email.mime.text import MIMEText
import os
from datetime import datetime

# ==============================================================================
# SECURE CONFIGURATION (ACCESSING GITHUB SECRETS)
# ==============================================================================
EMAIL_SENDER = os.environ["EMAIL_SENDER"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"] # Use Google App Password
EMAIL_RECEIVER = os.environ["EMAIL_RECEIVER"]

def get_automated_report():
    """Runs data checks and sends email dispatch."""
    try:
        # ENB Data
        enb = yf.Ticker("ENB.TO")
        price = enb.history(period="1d")["Close"].iloc[-1]
        div = enb.dividends.last("365D").sum()
        yld = (div / price) * 100
        
        # Nasdaq Data
        nasdaq = yf.Ticker("^IXIC")
        nas_hist = nasdaq.history(period="6mo")
        peak = nas_hist["Close"].max()
        current_nas = nas_hist["Close"].iloc[-1]
        drawdown = (current_nas - peak) / peak * 100
        
        # Determine signals for email body
        if yld >= 6.5: enb_a = "🔥 STRONG BUY"
        elif yld >= 5.8: enb_a = "✅ BUY MEDIUM"
        else: enb_a = "⏸️ HOLD (Yield < 5.8%)"
        
        if drawdown <= -10: tech_a = "✅ BUY MEDIUM TECH"
        else: tech_a = "⏸️ HOLD TECH"

        # Email composition
        body = f"""
Daily $1M Investment Check

{datetime.now().strftime('%Y-%m-%d Toronto')}

[ENB SIGNALS]
Yield: {yld:.2f}%
Action: {enb_a}

[TECH SIGNALS]
Nasdaq Drawdown: {drawdown:.2f}%
Action: {tech_a}

Check full dashboard for detailed execution plan.
"""
        msg = MIMEText(body)
        msg["Subject"] = "Daily Market Trigger Report"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            
        print("Dispatched daily alert email.")
        
    except Exception as e:
        print(f"Error executing bot: {e}")

if __name__ == "__main__":
    get_automated_report()