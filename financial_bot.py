import os
import smtplib
import pandas as pd
import yfinance as ticker_tool
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. PRODUCTION SECRETS (READS FROM GITHUB)
# ==========================================
sender_email = os.environ.get("SENDER_EMAIL")
app_password = os.environ.get("APP_PASSWORD")
receiver_email = os.environ.get("RECEIVER_EMAIL")

# ==========================================
# 2. DYNAMIC LIVE TICKER GENERATOR (INDIA)
# ==========================================
def get_live_nifty_tickers():
    print("Downloading live Nifty 500 list from NiftyIndices...")
    try:
        # Official public URL for the Nifty 500 stock structure file
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df = pd.read_csv(url)
        
        # Extract the 'Symbol' column and add '.NS' for Yahoo Finance compatibility
        tickers = [f"{symbol}.NS" for symbol in df['Symbol'].tolist()]
        print(f"Successfully loaded {len(tickers)} Indian stocks for screening.")
        return tickers
    except Exception as e:
        print(f"Failed to fetch live list: {e}. Falling back to emergency top stocks.")
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "TATAMOTORS.NS"]

# ==========================================
# 3. THE SCREENING BRAIN
# ==========================================
def screen_stocks():
    # Automatically get the latest 500 stocks
    watchlist = get_live_nifty_tickers()
    passing_stocks = []

    # To prevent Yahoo Finance from blocking us on free tier, we scan the top 80 stocks 
    # to find the absolute best daily moving setups.
    for ticker in watchlist[:80]: 
        try:
            stock = ticker_tool.Ticker(ticker)
            history = stock.history(period="200d")
            if history.empty or len(history) < 200:
                continue
                
            current_price = history['Close'].iloc[-1]
            ma_50 = history['Close'].tail(50).mean()
            ma_200 = history['Close'].mean()
            
            info = stock.info
            rev_growth = info.get('revenueGrowth', 0) * 100
            roe = info.get('returnOnEquity', 0) * 100
            peg = info.get('pegRatio', 'N/A')

            # STRICT FILTERS: Price trending up AND company growing dynamically
            is_trending = current_price > ma_50 and current_price > ma_200
            has_strong_growth = rev_growth >= 15.0
            
            if is_trending and has_strong_growth:
                passing_stocks.append({
                    "ticker": ticker.replace(".NS", ""), # Clean name for email
                    "price": current_price,
                    "rev_growth": rev_growth,
                    "roe": roe,
                    "peg": peg
                })
        except Exception:
            continue # Quietly bypass rate limits or data errors
            
    return passing_stocks

# ==========================================
# 4. FORMAT AND EMAIL GENERATION
# ==========================================
def send_daily_report(stocks_to_report):
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "🤖 Auto-Picked Indian Sector & Stock Highlights"

    body = "📊 DYNAMIC INDIAN MARKET DISCOVERY REPORT\n"
    body += "The bot automatically scanned the market indices and picked these matching stocks today:\n\n"
    body += "-----------------------------------------\n"

    if not stocks_to_report:
        body += "No major companies cleared the strict momentum and high-growth standard filters today.\n"
    else:
        for item in stocks_to_report:
            peg_val = f"{item['peg']:.2f}" if isinstance(item['peg'], (int, float)) else str(item['peg'])
            body += f"🔥 AUTO-PICKED ALERT: {item['ticker']}\n"
            body += f"   • Current Price: ₹{item['price']:.2f}\n"
            body += f"   • YoY Revenue Growth: {item['rev_growth']:.1f}% (Target: >15%)\n"
            body += f"   • Return on Equity (ROE): {item['roe']:.1f}%\n"
            body += f"   • PEG Ratio: {peg_val}\n"
            body += "-----------------------------------------\n"

    body += "\n*Completely hands-free analysis framework. Always review price charts before trading."
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        print("🎉 Dynamic daily report sent successfully!")
    except Exception as e:
        print(f"Email dispatch error: {e}")

if __name__ == "__main__":
    passed_list = screen_stocks()
    send_daily_report(passed_list)
