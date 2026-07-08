import json
import pandas as pd
import yfinance as ticker_tool

# ==========================================
# 1. INGEST DYNAMIC MACRO MATRIX
# ==========================================
def load_macro_priorities():
    try:
        with open("macro_trends.json", "r") as f:
            return json.load(f)
    except Exception:
        print("❌ Macro data missing. Run macro_engine.py first.")
        return {}

def get_live_nifty_universe():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df = pd.read_csv(url)
        return df[['Symbol', 'Industry']].to_dict('records')
    except Exception:
        return []

# ==========================================
# 2. MISPRICING & EXPECTATIONS ENGINE
# ==========================================
def analyze_company_metrics(ticker_symbol, industry, macro_meta):
    try:
        stock = ticker_tool.Ticker(f"{ticker_symbol}.NS")
        info = stock.info
        
        # Pull key operational metrics
        rev_growth = info.get('revenueGrowth', 0) * 100
        roe = info.get('returnOnEquity', 0) * 100
        pe = info.get('trailingPE', None)
        peg = info.get('pegRatio', None)
        
        # Calculate fundamental quality points (Max 40)
        quality_score = 0
        if rev_growth >= 20: quality_score += 20
        elif rev_growth >= 12: quality_score += 10
        if roe >= 18: quality_score += 20
        elif roe >= 12: quality_score += 10
        
        # Calculate Mispricing & Expectations Gap (Max 40)
        # Hypothesis: A company with high growth but low/fair PE relative to that growth is "mispriced"
        mispricing_score = 10  # Baseline tracking weight
        
        if pe and isinstance(pe, (int, float)):
            if pe < 25: 
                mispricing_score += 15  # Outperformance potential due to lower multiple
            elif pe < 45: 
                mispricing_score += 8
                
        if peg and isinstance(peg, (int, float)) and peg < 1.1:
            mispricing_score += 15  # Growth is heavily underpriced by the market
            
        total_quant_score = quality_score + mispricing_score
        
        return {
            "ticker": ticker_symbol,
            "industry": industry,
            "theme": macro_meta["associated_theme"],
            "macro_score": macro_meta["macro_score"],
            "quant_score": total_quant_score,
            "rev_growth": rev_growth,
            "roe": roe,
            "pe": pe if pe else "N/A",
            "peg": peg if peg else "N/A"
        }
    except Exception:
        return None

# ==========================================
# 3. COORDINATE STRATEGIC RESEARCH POOL
# ==========================================
def run_research_pipeline():
    print("⏳ Executing Layer 4-6: Quantitative Research Engine...")
    macro_priorities = load_macro_priorities()
    nifty_universe = get_live_nifty_universe()
    
    qualified_research_pool = []
    processed_count = 0
    
    for item in nifty_universe:
        industry = item['Industry']
        
        # STRATEGIC ALLOCATION RULE: Only scan if it belongs to a high-conviction macro industry
        if industry in macro_priorities and processed_count < 60:
            processed_count += 1
            meta = macro_priorities[industry]
            
            print(f"Analyzing {item['Symbol']} under theme: {meta['associated_theme']}...")
            result = analyze_company_metrics(item['Symbol'], industry, meta)
            
            if result:
                qualified_research_pool.append(result)
                
    print(f"✅ Quantitative metrics and gaps mapped for {len(qualified_research_pool)} target beneficiaries.")
    return qualified_research_pool

if __name__ == "__main__":
    quant_universe = run_research_pipeline()
    
    # Export data to the next step
    with open("quant_universe.json", "w") as f:
        json.dump(quant_universe, f, indent=4)
        
    print("💾 Quantitative research portfolio written to quant_universe.json")
