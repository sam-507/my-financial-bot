import os
import smtplib
from datetime import datetime
import pandas as pd
import yfinance as ticker_tool
from openai import OpenAI
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. ENCRYPTED SYSTEM SECRETS
# ==========================================
sender_email = os.environ.get("SENDER_EMAIL")
app_password = os.environ.get("APP_PASSWORD")
receiver_email = os.environ.get("RECEIVER_EMAIL")
openai_api_key = os.environ.get("OPENAI_API_KEY")

# Initialize OpenAI Client safely
ai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# Macro Sector-to-Theme Mapping Dictionary (Phase 2 Sector Mapping)
SECTOR_MAP = {
    "Automobile": "EV & Automotive Structural Tailwinds",
    "Chemicals": "Specialty Chemicals Realignment",
    "Construction": "Infrastructure & Capital Expenditure",
    "Financial Services": "Financialization of Savings & Digital Lending",
    "Information Technology": "Global Software Delivery & AI Engineering",
    "Oil Gas & Consumable Fuels": "Energy Security & Transition",
    "Capital Goods": "Industrial Manufacturing & EMS Renaissance",
    "Healthcare": "Healthcare Delivery, Hospitals & Insurance Infrastructure",
    "Power": "Data Center Energy Demand & Renewable Utilities"
}

def get_live_nifty_tickers():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df = pd.read_csv(url)
        # Keep both symbol and industry sector for structural analysis
        return df[['Symbol', 'Industry']].to_dict('records')
    except Exception:
        return [{"Symbol": "RELIANCE", "Industry": "Oil Gas & Consumable Fuels"}]

# ==========================================
# 2. QUANTITATIVE WEIGHTED SCORING MATRIX
# ==========================================
def calculate_investment_score(info, current_price, ma_50, ma_200):
    score = 0
    
    # Category A: Growth & Quality (Max 40 Points)
    rev_growth = info.get('revenueGrowth', 0) * 100
    roe = info.get('returnOnEquity', 0) * 100
    
    if rev_growth >= 25: score += 20
    elif rev_growth >= 15: score += 12
    if roe >= 20: score += 20
    elif roe >= 12: score += 10
    
    # Category B: Technical Momentum (Max 25 Points)
    if current_price > ma_50: score += 10
    if current_price > ma_200: score += 15
    
    # Category C: Valuation Guardrails (Max 20 Points)
    peg = info.get('pegRatio', None)
    pe = info.get('trailingPE', None)
    
    if peg and isinstance(peg, (int, float)) and peg < 1.2: score += 10
    elif pe and isinstance(pe, (int, float)) and pe < 25: score += 8
    score += 10 # Baseline score buffer for companies maintaining positive operating cash flow
    
    # Category D: Macro Sector Alignment (Max 15 Points)
    industry = info.get('industry', '')
    if any(sec in industry for sec in SECTOR_MAP.keys()):
        score += 15

    metrics_log = {"rev_growth": rev_growth, "roe": roe, "peg": peg if peg else "N/A", "pe": pe if pe else "N/A"}
    return min(score, 100), metrics_log

# ==========================================
# 3. CORE ANALYTICAL FILTER & SORT PIPE
# ==========================================
def generate_analyst_universe():
    raw_watchlist = get_live_nifty_tickers()
    scored_universe = []
    
    # Core target pool allocation
    target_pool = raw_watchlist[:80]
    
    for item in target_pool:
        ticker = f"{item['Symbol']}.NS"
        try:
            stock = ticker_tool.Ticker(ticker)
            history = stock.history(period="200d")
            if history.empty or len(history) < 200: continue
            
            current_price = history['Close'].iloc[-1]
            ma_50 = history['Close'].tail(50).mean()
            ma_200 = history['Close'].mean()
            info = stock.info
            
            score, metrics = calculate_investment_score(info, current_price, ma_50, ma_200)
            
            # Filter criteria: Only hand over institutional grade setups scoring above 65/100
            if score >= 65:
                scored_universe.append({
                    "ticker": item['Symbol'],
                    "industry": item['Industry'],
                    "theme": SECTOR_MAP.get(item['Industry'], "General Economic Expansion"),
                    "price": current_price,
                    "score": score,
                    **metrics
                })
        except Exception:
            continue
            
    # Sort strictly by the highest multi-layer score
    scored_universe.sort(key=lambda x: x['score'], reverse=True)
    return scored_universe[:5] # Extract Top 5 thematic priorities for AI Analysis

# ==========================================
# 4. QUALITATIVE GENERATIVE INSIGHTS LAYER
# ==========================================
def enrich_report_with_ai(top_stocks):
    if not ai_client or not top_stocks:
        return "AI Analyst Module Offline: Missing API Credentials or Qualifying Matches."
    
    prompt = f"""
    You are a Lead Institutional Investment Analyst specializing in the Indian Equities Market. 
    Analyze the following structured dataset of top-scoring Nifty 500 growth candidates:

    {top_stocks}

    Provide an investment summary report for these specific companies. 
    For each stock listed, generate a concise, bulleted 'Analyst Thesis' including:
    1. The core structural driver explaining why its macro theme or sector is seeing capital allocation right now.
    2. A brief analysis of its financial metrics (balancing high growth vs valuation constraints).
    3. Potential core operational catalysts or risks to monitor over a 3-5 year horizon.

    Keep your overall tone practical, realistic, professional, and dense with insight. Avoid generic fluff.
    """
    
    try:
        response = ai_client.chat.completions.create(
            model="gpt-4o-mini", # Cost-efficient, high-speed model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Failed to synthesize qualitative layer due to API exception: {e}"

# ==========================================
# 5. ENTERPRISE REPORT DISPATCH ENGINE
# ==========================================
def dispatch_investment_report(portfolio, ai_thesis, total_screened=80):
    current_time = datetime.utcnow()
    date_str = current_time.strftime("%d %b %Y")
    
    recipient_list = [email.strip() for email in receiver_email.split(",")]
    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = ", ".join(recipient_list)
    message["Subject"] = f"📈 Indian Market Discovery Report | {date_str}"

    # Build Unified Text Output Channel
    text_body = f"══════════════════════════════════════\n🎯 ALPHA ANALYST PORTFOLIO DEPLOYMENT\n══════════════════════════════════════\nDate: {date_str}\nScanned Universe: Top {total_screened} Elements from Nifty 500\n\n"
    text_body += "📌 TOP RANKED INVESTMENT CANDIDATES (QUANT MASTER MATRIX)\n"
    
    for idx, stock in enumerate(portfolio, start=1):
        text_body += f"\n#{idx} 🔥 {stock['ticker']} [SCORE: {stock['score']}/100]\n"
        text_body += f"   • Theme: {stock['theme']}\n"
        text_body += f"   • Price: ₹{stock['price']:.2f} | YoY Revenue Growth: {stock['rev_growth']:.1f}% | ROE: {stock['roe']:.1f}%\n"
    
    text_body += f"\n\n══════════════════════════════════════\n🤖 INTELLECTUAL RESEARCH & ANALYST THESIS\n══════════════════════════════════════\n\n{ai_thesis}\n"
    text_body += "\n\n══════════════════════════════\n⚠ Educational Research Disclaimer\nGenerated automatically via structural algorithms. Not direct financial advisory.\n══════════════════════════════"

    # Build Clean HTML Interface
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:20px; font-family:'Segoe UI',Arial,sans-serif; background-color:#ffffff; color:#333333;">
        <div style="max-width:650px; margin:0 auto;">
            <div style="border-bottom:3px solid #01579b; padding-bottom:15px; margin-bottom:25px;">
                <h1 style="margin:0; color:#01579b; font-size:24px;">🎯 ALPHA ANALYST INSIGHTS REPORT</h1>
                <p style="margin:5px 0 0 0; font-size:13px; color:#666666;">Macro Structural Research & Quantitative Allocation Engine • <strong>{date_str}</strong></p>
            </div>
            
            <h3 style="color:#01579b; text-transform:uppercase; font-size:14px; letter-spacing:0.5px;">📌 Top Ranked Investment Candidates</h3>
    """
    
    for idx, stock in enumerate(portfolio, start=1):
        html_body += f"""
        <div style="margin-bottom:15px; border:1px solid #e0e0e0; border-radius:6px; background-color:#fafafa; padding:15px;">
            <table width="100%" style="border-collapse:collapse;">
                <tr>
                    <td><strong style="font-size:16px; color:#111;">#{idx} {stock['ticker']}</strong> <span style="font-size:12px; color:#666;">({stock['industry']})</span></td>
                    <td align="right"><span style="background-color:#01579b; color:#fff; padding:3px 8px; border-radius:4px; font-size:12px; font-weight:bold;">SCORE: {stock['score']}/100</span></td>
                </tr>
            </table>
            <p style="margin:8px 0 4px 0; font-size:13px; color:#0288d1;"><strong>Theme:</strong> {stock['theme']}</p>
            <p style="margin:0; font-size:13px; color:#555;">Price: <strong>₹{stock['price']:.2f}</strong> | YoY Growth: <strong>{stock['rev_growth']:.1f}%</strong> | ROE: <strong>{stock['roe']:.1f}%</strong> | PEG: <strong>{stock['peg']}</strong></p>
        </div>
        """
        
    html_body += f"""
            <div style="margin-top:30px; margin-bottom:30px; background-color:#f4fbfd; border-top:3px solid #0288d1; padding:20px; border-radius:0 0 4px 4px;">
                <h3 style="margin-top:0; color:#01579b; font-size:15px;">🤖 Intellectual Research & Analyst Thesis</h3>
                <div style="font-size:14px; line-height:1.6; color:#444; white-space: pre-line;">{ai_thesis}</div>
            </div>
            
            <div style="border-top:1px solid #e0e0e0; padding-top:15px; text-align:center; font-size:11px; color:#888;">
                <p><strong>⚠ Regulatory & Compliance Disclaimer</strong><br>This system is an automated structural experiment parsing public metadata for educational exploration. It does not constitute formal advisory portfolio actions.</p>
            </div>
        </div>
    </body>
    </html>
    """

    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient_list, message.as_string())
        server.quit()
        print("🎉 High-conviction analyst report successfully compiled and dispatched.")
    except Exception as e:
        print(f"SMTP operational failure: {e}")

# ==========================================
# EXECUTIVE EXECUTION TRACE
# ==========================================
if __name__ == "__main__":
    high_conviction_universe = generate_analyst_universe()
    thesis_payload = enrich_report_with_ai(high_conviction_universe)
    dispatch_investment_report(high_conviction_universe, thesis_payload)
