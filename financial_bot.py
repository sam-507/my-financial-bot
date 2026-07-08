import os
import json
import smtplib
from datetime import datetime
import yfinance as ticker_tool
from openai import OpenAI
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. CORE OPERATIONAL SECRETS
# ==========================================
sender_email = os.environ.get("SENDER_EMAIL")
app_password = os.environ.get("APP_PASSWORD")
receiver_email = os.environ.get("RECEIVER_EMAIL")
openai_api_key = os.environ.get("OPENAI_API_KEY")

ai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None

def load_quantitative_universe():
    try:
        with open("quant_universe.json", "r") as f:
            return json.load(f)
    except Exception:
        print("❌ Quantitative data missing. Run research_engine.py first.")
        return []

# ==========================================
# 2. DECISION MATRIX & CONFIRMATION ENGINE
# ==========================================
def process_final_rankings():
    print("⏳ Executing Layer 7-8: Final Decision & Confirmation Engine...")
    quant_universe = load_quantitative_universe()
    final_portfolio = []
    
    for company in quant_universe:
        ticker = f"{company['ticker']}.NS"
        try:
            stock = ticker_tool.Ticker(ticker)
            history = stock.history(period="200d")
            if history.empty or len(history) < 200: continue
            
            current_price = history['Close'].iloc[-1]
            ma_50 = history['Close'].tail(50).mean()
            ma_200 = history['Close'].mean()
            
            # Layer 8: Market Confirmation Score (Max 20 Points)
            # Check if the stock is supported by an active long-term uptrend structure
            confirmation_score = 0
            if current_price > ma_50: confirmation_score += 10
            if current_price > ma_200: confirmation_score += 10
            
            # Compile Final Combined Weighted Score
            # Weight Distribution: Macro Tailwind (20%) + Company & Mispricing (40%) + Technical Confirmation (20%) + Baseline Catalyst Space (20%)
            macro_weighted = (company['macro_score'] / 100) * 20
            quant_weighted = (company['quant_score'] / 80) * 40
            tech_weighted = confirmation_score
            baseline_catalyst = 15 # Placeholder buffer for qualitative structural triggers
            
            final_score = int(macro_weighted + quant_weighted + tech_weighted + baseline_catalyst)
            
            final_portfolio.append({
                "ticker": company['ticker'],
                "industry": company['industry'],
                "theme": company['theme'],
                "price": current_price,
                "rev_growth": company['rev_growth'],
                "roe": company['roe'],
                "pe": company['pe'],
                "peg": company['peg'],
                "score": min(final_score, 100)
            })
        except Exception:
            continue
            
    # Sort strictly by the highest conviction score and extract the top 10 positions
    final_portfolio.sort(key=lambda x: x['score'], reverse=True)
    return final_portfolio[:10]

# ==========================================
# 3. GENERATIVE RESEARCH SYNTHESIS LAYER
# ==========================================
def generate_ai_analyst_notes(portfolio):
    if not ai_client or not portfolio:
        return "AI Inference Engine Offline: Missing configuration parameters."
    
    prompt = f"""
    You are a Senior Buy-Side Equity Research Analyst evaluating allocations for a ₹1 Lakh long-term retail portfolio.
    Analyze the following top-scoring Nifty 500 opportunities:
    
    {portfolio}
    
    Format a highly professional research report. For each of the listed companies, write a dense, scannable summary covering:
    1. 'Investment Thesis': Why its macro theme or industry is experiencing sudden structural expansion.
    2. 'Why Now & Catalysts': Identify high-probability corporate or regulatory catalysts (e.g., capacity expansion, government order pipelines, falling input costs, or an unappreciated growth-adjusted valuation).
    3. 'Risks to Monitor': Core threats that could break the long-term 3-5 year thesis.
    
    Maintain a factual, objective tone. Do not use generic market filler text.
    """
    
    try:
        response = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI generation layer error: {e}"

# ==========================================
# 4. ENTERPRISE DELIVERY ENGINE
# ==========================================
def dispatch_newsletter(portfolio, ai_thesis):
    current_time = datetime.utcnow()
    date_str = current_time.strftime("%d %b %Y")
    
    recipient_list = [email.strip() for email in receiver_email.split(",")]
    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = ", ".join(recipient_list)
    message["Subject"] = f"🎯 Daily Hypothesis Portfolio Alpha | {date_str}"

    # Text fall-back structure
    text_body = f"══════════════════════════════════════\n🎯 HYPOTHESIS INVESTMENT RECOMMENDATION ENGINE\n══════════════════════════════════════\nDate: {date_str}\n\n"
    for idx, stock in enumerate(portfolio, start=1):
        text_body += f"#{idx} 🔥 {stock['ticker']} [CONVICTION: {stock['score']}/100]\n"
        text_body += f"   • Theme: {stock['theme']}\n"
        text_body += f"   • Metrics: Price: ₹{stock['price']:.2f} | Growth: {stock['rev_growth']:.1f}% | ROE: {stock['roe']:.1f}% | PE: {stock['pe']}\n"
    text_body += f"\n\nANALYST RESEARCH THESIS & RISKS:\n\n{ai_thesis}"

    # Professional HTML view
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:20px; font-family:'Segoe UI',Arial,sans-serif; background-color:#ffffff; color:#333333;">
        <div style="max-width:650px; margin:0 auto;">
            <div style="border-bottom:3px solid #006064; padding-bottom:15px; margin-bottom:25px;">
                <h1 style="margin:0; color:#006064; font-size:22px;">🎯 HIGH-CONVICTION PROBABILISTIC PORTFOLIO</h1>
                <p style="margin:5px 0 0 0; font-size:13px; color:#666666;">Optimal Risk-Reward Hypotheses for a 3-5 Year Horizon • <strong>{date_str}</strong></p>
            </div>
            
            <div style="background-color:#fffde7; border:1px solid #fff59d; padding:12px; font-size:13px; color:#5d4037; border-radius:4px; margin-bottom:25px;">
                <strong>💡 Allocation Strategy:</strong> This report outlines top ideas matching the structural macro model, sorted dynamically by our multi-layered hypothesis network.
            </div>
    """
    
    for idx, stock in enumerate(portfolio, start=1):
        html_body += f"""
        <div style="margin-bottom:20px; border:1px solid #e0e0e0; border-radius:6px; background-color:#fafafa; overflow:hidden;">
            <div style="background-color:#e0f7fa; padding:10px 15px; border-bottom:1px solid #e0e0e0;">
                <table width="100%" style="border-collapse:collapse;">
                    <tr>
                        <td><strong style="font-size:15px; color:#006064;">#{idx} {stock['ticker']}</strong> <span style="font-size:11px; color:#555;">({stock['industry']})</span></td>
                        <td align="right"><span style="background-color:#006064; color:#fff; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:bold;">SCORE: {stock['score']}/100</span></td>
                    </tr>
                </table>
            </div>
            <div style="padding:12px 15px; font-size:13px; color:#444;">
                <p style="margin:0 0 6px 0;"><strong>Macro Tailwind:</strong> {stock['theme']}</p>
                <p style="margin:0;">Price: <strong>₹{stock['price']:.2f}</strong> | YoY Growth: <strong>{stock['rev_growth']:.1f}%</strong> | ROE: <strong>{stock['roe']:.1f}%</strong> | PE: <strong>{stock['pe']}</strong> | PEG: <strong>{stock['peg']}</strong></p>
            </div>
        </div>
        """
        
    html_body += f"""
            <div style="margin-top:30px; background-color:#fcfcfc; border-top:3px solid #006064; padding:20px; border-radius:4px; box-shadow:inset 0 1px 3px rgba(0,0,0,0.02);">
                <h3 style="margin-top:0; color:#006064; font-size:15px; text-transform:uppercase;">📝 Deep Equity Research & Analyst Notes</h3>
                <div style="font-size:13.5px; line-height:1.6; color:#444; white-space: pre-line;">{ai_thesis}</div>
            </div>
            
            <div style="margin-top:40px; border-top:1px solid #e0e0e0; padding-top:15px; text-align:center; font-size:10.5px; color:#888; line-height:1.5;">
                <p><strong>⚠ Regulatory & Compliance Disclaimer</strong><br>
                This automated system calculates directional investment probabilities for educational purposes. It does not provide definitive asset price predictions or individualized investment management advice. Past structural performance metrics do not guarantee forward-looking realization.</p>
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
        print("🎉 Modular Multi-Engine report safely delivered to all endpoints.")
    except Exception as e:
        print(f"SMTP delivery error: {e}")

# ==========================================
# SYSTEM ORCHESTRATION MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    validated_portfolio = process_final_rankings()
    analyst_thesis = generate_ai_analyst_notes(validated_portfolio)
    dispatch_newsletter(validated_portfolio, analyst_thesis)
