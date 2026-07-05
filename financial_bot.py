import smtplib
import yfinance as ticker_tool
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. YOUR CREDENTIALS (FILL THESE IN)
# ==========================================
import os
import smtplib
import yfinance as ticker_tool
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. PRODUCTION SECRETS (READS FROM GITHUB)
# ==========================================
sender_email = os.environ.get("SENDER_EMAIL")
app_password = os.environ.get("APP_PASSWORD")
receiver_email = os.environ.get("RECEIVER_EMAIL")

# The rest of your code remains exactly the same...

# The list of stocks you want your bot to screen daily
watchlist = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", "NFLX"]

# ==========================================
# 2. THE SCREENING BRAIN
# ==========================================
def screen_stocks():
    print("Starting daily market scan...")
    passing_stocks = []

    for ticker in watchlist:
        try:
            print(f"Analyzing {ticker}...")
            stock = ticker_tool.Ticker(ticker)
            
            # Fetch price history for technical trend metrics
            history = stock.history(period="200d")
            if history.empty:
                continue
                
            current_price = history['Close'].iloc[-1]
            ma_50 = history['Close'].tail(50).mean()
            ma_200 = history['Close'].mean()
            
            # Fetch company details for fundamental standards
            info = stock.info
            rev_growth = info.get('revenueGrowth', 0) * 100
            roe = info.get('returnOnEquity', 0) * 100
            peg = info.get('pegRatio', 'N/A')

            # --- INDUSTRY STANDARD FILTERS ---
            # Rule 1: Stock must be in a healthy uptrend (Price above 50-day and 200-day averages)
            is_trending = current_price > ma_50 and current_price > ma_200
            
            # Rule 2: Strong growth (Revenue growth greater than 15%)
            has_strong_growth = rev_growth >= 15.0
            
            # If it passes both rules, add it to our daily report!
            if is_trending and has_strong_growth:
                passing_stocks.append({
                    "ticker": ticker,
                    "price": current_price,
                    "rev_growth": rev_growth,
                    "roe": roe,
                    "peg": peg
                })
        except Exception as e:
            print(f"Skipping {ticker} due to error: {e}")
            
    return passing_stocks

# ==========================================
# 3. FORMAT AND EMAIL GENERATION
# ==========================================
def send_daily_report(stocks_to_report):
    # Draft the email header
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "🤖 Your Daily 2-Minute Directional Read"

    # Build the scannable text body
    body = "📊 DAILY FINANCIAL DIRECTIONAL REPORT\n"
    body += "Here are the stocks displaying strong industry standard fundamentals and positive momentum today:\n\n"
    body += "-----------------------------------------\n"

    if not stocks_to_report:
        body += "No stocks met the baseline growth and momentum criteria today. Standing aside.\n"
    else:
        for item in stocks_to_report:
            # Safely format PEG ratio string/float
            peg_val = f"{item['peg']:.2f}" if isinstance(item['peg'], (int, float)) else str(item['peg'])
            
            body += f"🔥 STOCK LOOKOUT: {item['ticker']}\n"
            body += f"   • Current Price: ${item['price']:.2f}\n"
            body += f"   • YoY Revenue Growth: {item['rev_growth']:.1f}% (Target: >15%)\n"
            body += f"   • Return on Equity: {item['roe']:.1f}%\n"
            body += f"   • PEG Ratio: {peg_val}\n"
            body += "-----------------------------------------\n"

    body += "\n*This is an automated operational checklist read. Verify charts before placing capital."
    message.attach(MIMEText(body, "plain"))

    # Connect to server and dispatch
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        print("🎉 Daily report successfully generated and emailed!")
    except Exception as e:
        print(f"Email failed to send: {e}")

# ==========================================
# RUN THE ENGINE
# ==========================================
if __name__ == "__main__":
    passed_list = screen_stocks()
    send_daily_report(passed_list)
