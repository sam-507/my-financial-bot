import os
import smtplib
from datetime import datetime
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
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df = pd.read_csv(url)
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
    watchlist = get_live_nifty_tickers()
    passing_stocks = []
    stocks_screened_count = 0

    # Screening target limit remains exactly 80
    target_pool = watchlist[:80]
    
    for ticker in target_pool:
        try:
            stock = ticker_tool.Ticker(ticker)
            history = stock.history(period="200d")
            if history.empty or len(history) < 200:
                continue
                
            stocks_screened_count += 1
            current_price = history['Close'].iloc[-1]
            ma_50 = history['Close'].tail(50).mean()
            ma_200 = history['Close'].mean()
            
            info = stock.info
            rev_growth = info.get('revenueGrowth', 0) * 100
            roe = info.get('returnOnEquity', 0) * 100
            peg = info.get('pegRatio', 'N/A')

            # Core business criteria remains unchanged
            is_trending = current_price > ma_50 and current_price > ma_200
            has_strong_growth = rev_growth >= 15.0
            
            if is_trending and has_strong_growth:
                passing_stocks.append({
                    "ticker": ticker.replace(".NS", ""),
                    "price": current_price,
                    "rev_growth": rev_growth,
                    "roe": roe,
                    "peg": peg
                })
        except Exception:
            continue
            
    return passing_stocks, stocks_screened_count

# ==========================================
# 4. FORMAT AND EMAIL GENERATION
# ==========================================
def send_daily_report(stocks_to_report, total_screened):
    # Dynamic Date Handling
    current_time = datetime.utcnow()
    date_str = current_time.strftime("%d %b %Y")
    time_str = current_time.strftime("%H:%M UTC")

    # Success rate metrics calculations
    matches_found = len(stocks_to_report)
    success_rate = (matches_found / total_screened * 100) if total_screened > 0 else 0

    # Multi-recipient parsing logic preserved
    recipient_list = [email.strip() for email in receiver_email.split(",")]

    # Initialize container for matching HTML & Plain Text distribution
    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = ", ".join(recipient_list)
    message["Subject"] = f"📈 Indian Market Discovery Report | {date_str}"

    # -------------------------------------------------------------------------
    # FORMAT A: PLAIN TEXT VERSION
    # -------------------------------------------------------------------------
    text_body = "══════════════════════════════════════\n"
    text_body += "📈 INDIAN MARKET DISCOVERY REPORT\n"
    text_body += "══════════════════════════════════════\n\n"
    text_body += f"📅 Report Date:\n{date_str}\n\n"
    text_body += f"🕘 Generated At:\n{time_str}\n\n"
    text_body += "📊 Universe Scanned:\nTop 80 stocks from Nifty 500\n\n"
    text_body += "✅ Screening Criteria\n• Price > 50 DMA\n• Price > 200 DMA\n• Revenue Growth ≥ 15%\n\n"
    text_body += "-----------------------------------------\n\n"
    text_body += "📌 MARKET SUMMARY\n\n"
    text_body += f"Stocks Screened: {total_screened}\n"
    text_body += f"Matches Found: {matches_found}\n"
    text_body += f"Success Rate: {success_rate:.1f}%\n\n"
    text_body += "-----------------------------------------\n\n"

    if not stocks_to_report:
        text_body += "No major companies cleared the strict momentum and high-growth standard filters today.\n"
    else:
        for idx, item in enumerate(stocks_to_report, start=1):
            peg_val = f"{item['peg']:.2f}" if isinstance(item['peg'], (int, float)) else str(item['peg'])
            text_body += "━━━━━━━━━━━━━━━━━━━━━━\n"
            text_body += f"#{idx} 🔥 {item['ticker']}\n\n"
            text_body += f"💰 Price: ₹{item['price']:.2f}\n"
            text_body += f"📈 Revenue Growth: {item['rev_growth']:.1f}%\n"
            text_body += f"🏆 ROE: {item['roe']:.1f}%\n"
            text_body += f"📊 PEG: {peg_val}\n"
            text_body += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

    text_body += "══════════════════════════════\n\n"
    text_body += "⚠ Disclaimer\n\n"
    text_body += "This report is automatically generated using publicly available market data.\n\n"
    text_body += "It is intended for educational and research purposes only and should not be considered investment advice.\n\n"
    text_body += "Always perform your own due diligence before investing.\n\n"
    text_body += "══════════════════════════════"

    # -------------------------------------------------------------------------
    # FORMAT B: HTML VERSION
    # -------------------------------------------------------------------------
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Indian Market Discovery Report</title>
    </head>
    <body style="margin: 0; padding: 20px; background-color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; color: #333333; -webkit-font-smoothing: antialiased;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
            
            <div style="border: 2px double #0288d1; padding: 20px; text-align: center; background-color: #f4fbfd; margin-bottom: 25px;">
                <h1 style="margin: 0; font-size: 22px; color: #0288d1; letter-spacing: 1px; font-weight: 700;">📈 INDIAN MARKET DISCOVERY REPORT</h1>
            </div>
            
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 25px; border-collapse: collapse;">
                <tr>
                    <td width="50%" style="vertical-align: top; padding-right: 10px;">
                        <p style="margin: 0 0 5px 0; font-size: 12px; text-transform: uppercase; color: #777777; font-weight: bold; letter-spacing: 0.5px;">📅 Report Date</p>
                        <p style="margin: 0 0 15px 0; font-size: 15px; font-weight: 600; color: #111111;">{date_str}</p>
                        
                        <p style="margin: 0 0 5px 0; font-size: 12px; text-transform: uppercase; color: #777777; font-weight: bold; letter-spacing: 0.5px;">🕘 Generated At</p>
                        <p style="margin: 0 0 15px 0; font-size: 15px; font-weight: 600; color: #111111;">{time_str}</p>
                    </td>
                    <td width="50%" style="vertical-align: top; padding-left: 10px; border-left: 1px solid #e0e0e0;">
                        <p style="margin: 0 0 5px 0; font-size: 12px; text-transform: uppercase; color: #777777; font-weight: bold; letter-spacing: 0.5px;">📊 Universe Scanned</p>
                        <p style="margin: 0 0 15px 0; font-size: 14px; font-weight: 600; color: #111111;">Top 80 stocks from Nifty 500</p>
                        
                        <p style="margin: 0 0 5px 0; font-size: 12px; text-transform: uppercase; color: #777777; font-weight: bold; letter-spacing: 0.5px;">✅ Screening Criteria</p>
                        <ul style="margin: 0; padding: 0 0 0 15px; font-size: 13px; color: #444444; line-height: 1.4;">
                            <li style="margin-bottom: 2px;">Price &gt; 50 DMA</li>
                            <li style="margin-bottom: 2px;">Price &gt; 200 DMA</li>
                            <li style="margin-bottom: 0;">Revenue Growth &ge; 15%</li>
                        </ul>
                    </td>
                </tr>
            </table>

            <div style="background-color: #f8f9fa; border-left: 4px solid #0288d1; padding: 15px; margin-bottom: 30px; border-radius: 4px;">
                <h3 style="margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; color: #0288d1; font-weight: bold; letter-spacing: 0.5px;">📌 MARKET SUMMARY</h3>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="font-size: 14px; color: #444444;">
                    <tr>
                        <td style="padding: 3px 0;">Stocks Screened:</td>
                        <td align="right" style="font-weight: bold; color: #111111;">{total_screened}</td>
                    </tr>
                    <tr>
                        <td style="padding: 3px 0;">Matches Found:</td>
                        <td align="right" style="font-weight: bold; color: #111111;">{matches_found}</td>
                    </tr>
                    <tr>
                        <td style="padding: 3px 0;">Success Rate:</td>
                        <td align="right" style="font-weight: bold; color: #0288d1;">{success_rate:.1f}%</td>
                    </tr>
                </table>
            </div>

            """

    if not stocks_to_report:
        html_body += """
            <div style="text-align: center; padding: 30px; border: 1px dashed #cccccc; color: #666666; font-size: 14px; border-radius: 4px;">
                No major companies cleared the strict momentum and high-growth standard filters today.
            </div>
        """
    else:
        for idx, item in enumerate(stocks_to_report, start=1):
            peg_val = f"{item['peg']:.2f}" if isinstance(item['peg'], (int, float)) else str(item['peg'])
            html_body += f"""
            <div style="margin-bottom: 20px; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="background-color: #f4fbfd; padding: 12px 15px; border-bottom: 1px solid #e0e0e0;">
                    <h4 style="margin: 0; font-size: 15px; color: #111111; font-weight: bold;">#{idx} 🔥 {item['ticker']}</h4>
                </div>
                <div style="padding: 15px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="font-size: 14px; color: #555555;">
                        <tr>
                            <td style="padding: 4px 0;">💰 Price:</td>
                            <td align="right" style="font-weight: 600; color: #111111;">₹{item['price']:.2f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0;">📈 Revenue Growth:</td>
                            <td align="right" style="font-weight: 600; color: #2e7d32;">{item['rev_growth']:.1f}%</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0;">🏆 ROE:</td>
                            <td align="right" style="font-weight: 600; color: #111111;">{item['roe']:.1f}%</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0;">📊 PEG:</td>
                            <td align="right" style="font-weight: 600; color: #111111;">{peg_val}</td>
                        </tr>
                    </table>
                </div>
            </div>
            """

    # Structured Professional Footer Block
    html_body += """
            <div style="margin-top: 35px; border-top: 1px solid #e0e0e0; padding-top: 20px; text-align: center; font-size: 11px; color: #777777; line-height: 1.6;">
                <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: bold; color: #555555; text-transform: uppercase; letter-spacing: 0.5px;">⚠ Disclaimer</p>
                <p style="margin: 0 0 8px 0;">This report is automatically generated using publicly available market data.</p>
                <p style="margin: 0 0 8px 0;">It is intended for educational and research purposes only and should not be considered investment advice.</p>
                <p style="margin: 0;">Always perform your own due diligence before investing.</p>
            </div>
            
        </div>
    </body>
    </html>
    """

    # Attach alternate plain and layout views
    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient_list, message.as_string())
        server.quit()
        print("🎉 Clean UX daily report sent successfully to all recipients!")
    except Exception as e:
        print(f"Email dispatch error: {e}")

# ==========================================
# RUN THE ENGINE
# ==========================================
if __name__ == "__main__":
    passed_list, screened_count = screen_stocks()
    send_daily_report(passed_list, screened_count)
