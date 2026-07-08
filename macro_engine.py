import json

# ==========================================
# 1. THEMATIC KNOWLEDGE GRAPH & BENEFICIARY MAP
# ==========================================
# This maps macro themes directly to second-order target industries listed in the Nifty 500
THEME_KNOWLEDGE_BASE = {
    "Power & Data Center Surge": {
        "score": 95,
        "rationale": "Sustained peak power deficits driven by industrial expansion and AI data center installations.",
        "target_industries": ["Power", "Capital Goods", "Cables", "Industrial Products"]
    },
    "Defense & Aerospace Localization": {
        "score": 92,
        "rationale": "Aggressive capital expenditure allocations from the defense budget focused strictly on domestic production.",
        "target_industries": ["Aerospace & Defence", "Capital Goods", "Industrial Manufacturing"]
    },
    "EMS & Electronics Manufacturing": {
        "score": 88,
        "rationale": "Global supply chain realignments combined with domestic production-linked incentives (PLI schemes).",
        "target_industries": ["Industrial Products", "Consumer Durables", "Electronic Components"]
    },
    "Infrastructure & Railways Capex": {
        "score": 85,
        "rationale": "Multi-year government budgetary deployments for freight corridors, high-speed lines, and track modernizations.",
        "target_industries": ["Construction", "Iron & Steel", "Cables", "Engineering Services"]
    },
    "Financialization of Savings": {
        "score": 80,
        "rationale": "Structural shift of retail wealth out of real estate/gold and directly into asset management platforms.",
        "target_industries": ["Financial Services", "Capital Markets"]
    }
}

# ==========================================
# 2. SECTOR PRIORITY COMPILATION
# ==========================================
def compile_macro_priorities():
    print("⏳ Executing Layer 1-3: Macro Intelligence Engine...")
    
    favored_industries = {}
    
    # Process the knowledge base to assign weighted scores to raw industries
    for theme, details in THEME_KNOWLEDGE_BASE.items():
        theme_score = details["score"]
        for industry in details["target_industries"]:
            # If an industry benefits from multiple themes, take the highest score
            if industry in favored_industries:
                if theme_score > favored_industries[industry]["macro_score"]:
                    favored_industries[industry]["macro_score"] = theme_score
            else:
                favored_industries[industry] = {
                    "associated_theme": theme,
                    "macro_score": theme_score,
                    "theme_rationale": details["rationale"]
                }
                
    print(f"✅ Macro map established. {len(favored_industries)} core industries prioritized.")
    return favored_industries

# ==========================================
# 3. EXPORT PIPELINE DATA BOUNDARY
# ==========================================
if __name__ == "__main__":
    macro_data = compile_macro_priorities()
    
    # Save the output to a temporary JSON file so the Research Engine can read it
    with open("macro_trends.json", "w") as f:
        json.dump(macro_data, f, indent=4)
        
    print("💾 Macro priority matrix safely written to macro_trends.json")
