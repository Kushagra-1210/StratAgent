import os
import datetime
import requests
import feedparser
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from newspaper import Article
from fpdf import FPDF
import urllib.parse
import re
import numpy as np
import matplotlib.pyplot as plt

class StratAgentPDF(FPDF):
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Helvetica italic 8
        self.set_font("Helvetica", "I", 8)
        # Page number and date footer
        footer_text = f"StratAgent | Generated {datetime.datetime.now().strftime('%Y-%m-%d')} | Data: Screener.in, Google News | Page {self.page_no()}"
        self.cell(0, 10, footer_text, align="C")

load_dotenv()

# --- MCKINSEY STYLE CONSTANTS ---
MCKINSEY_BLUE = "#2251FF"
MCKINSEY_DARK = "#1a1a1a"
MCKINSEY_GRAY = "#6b7280"
MCKINSEY_LIGHT_GRAY = "#f3f4f6"
MCKINSEY_GREEN = "#16a34a"
MCKINSEY_RED = "#dc2626"
MCKINSEY_AMBER = "#f59e0b"


def apply_mckinsey_style(ax):
    """Apply McKinsey styling to matplotlib axes."""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#e5e7eb')
    ax.spines['bottom'].set_color('#e5e7eb')
    ax.tick_params(colors=MCKINSEY_GRAY, labelsize=9)
    ax.yaxis.grid(True, color='#e5e7eb', linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.xaxis.label.set_color(MCKINSEY_GRAY)
    ax.xaxis.label.set_fontsize(9)


def sanitize_for_pdf_render(text: str) -> str:
    """
    Final sanitization pass right before PDF rendering.
    Ensures absolutely no non-ASCII characters reach FPDF.
    """
    # Unicode replacements (quick catch for any that slipped through)
    unicode_map = {
        '≥': '>=', '≤': '<=', '→': '->', '←': '<-', '×': 'x',
        '÷': '/', '±': '+/-', '≈': '~', '≠': '!=', '∞': 'inf',
        '√': 'sqrt', '°': 'deg', '™': '(TM)', '®': '(R)',
        '©': '(C)', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₹': 'INR',
        '•': '-', '–': '-', '—': '-', '“': '"', '”': '"',
        '‘': "'", '’': "'",
    }
    
    for unicode_char, replacement in unicode_map.items():
        text = text.replace(unicode_char, replacement)
    
    # Final nuclear option: Strip everything that's not ASCII
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    return text


def clean_for_pdf(text: str) -> str:
    """
    Remove all internal scaffolding tags before PDF rendering.
    Machine-readable tags are removed entirely.
    Also sanitizes Unicode characters that Helvetica font can't render.
    """
    blocks_to_remove = [
        r"COMPANY_CLASSIFICATION:.*?Classification_Type:.*?\n",
        r"OPTION_SCORES:.*?(?=\n\n|\n##|\nFinancial|$)",
        r"WATERFALL:.*?\n",
        r"PULLQUOTE:.*?\n",
        r"EXHIBIT \d+:.*?\n",
        r"## METRICS FOR CHART.*?PE:.*?\n",
        r"--- STRATAGENT ANALYTICS APPENDIX ---.*?(?=$)",
        r"\n(FINANCIAL ANGLE:|MARKET ANGLE:|STRATEGIC ANGLE:|CUSTOMER ANGLE:|OPERATIONAL/FEASIBILITY ANGLE:|RISK ANGLE:|ROADMAP:).*?(?=\n##|\n\n|$)",
        r"Pros:.*?(?=\n\n|\n[A-Z]|$)",
        r"Cons:.*?(?=\n\n|\n[A-Z]|$)",
    ]
    
    for pattern in blocks_to_remove:
        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove raw dict-like outputs (e.g., {'key': value})
    text = re.sub(r"\{\s*['\"]?\w+['\"]?\s*:\s*[\d.]+\s*(?:,\s*['\"]?\w+['\"]?\s*:\s*[\d.]+\s*)*\}", "", text)
    
    # Remove ====== dividers completely
    text = re.sub(r"={3,}", "", text)
    
    # Sanitize Unicode characters that Helvetica can't render
    unicode_replacements = {
        '≥': '>=',
        '≤': '<=',
        '→': '->',
        '←': '<-',
        '×': 'x',
        '÷': '/',
        '±': '+/-',
        '≈': '~',
        '≠': '!=',
        '∞': 'inf',
        '√': 'sqrt',
        '°': ' deg ',
        '™': '(TM)',
        '®': '(R)',
        '©': '(C)',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
        '₹': 'INR',
        '•': '-',
        '–': '-',
        '—': '-',
        '“': '"',
        '”': '"',
        '‘': "'",
        '’': "'",
    }
    
    for unicode_char, replacement in unicode_replacements.items():
        text = text.replace(unicode_char, replacement)
    
    # Final aggressive step: remove any remaining non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    return text.strip()

def fetch_article_text(url: str) -> str:
    try:
        if 'news.google.com' in url:
            return "Data unavailable: Google News URLs cannot be decoded directly."
        article = Article(url)
        article.download()
        article.parse()
        if not article.text:
            return "Data unavailable: Could not extract article text."
        return article.text[:2000]
    except Exception as e:
        return f"Data unavailable: Could not fetch article. ({e})"

import urllib.parse

def fetch_news(company_name: str) -> str:
    try:
        # Primary source: Mint RSS filtered by company name
        mint_url = "https://www.livemint.com/rss/companies"
        feed = feedparser.parse(mint_url)
        
        # Filter entries where company name appears in title
        filtered = [
            e for e in feed.entries 
            if company_name.lower() in e.get('title', '').lower()
        ]
        
        # Fallback: Google News RSS if Mint has no matches
        source_used = "Mint"
        if not filtered:
            encoded_company = urllib.parse.quote(company_name)
            google_url = f"https://news.google.com/rss/search?q={encoded_company}&hl=en-IN&gl=IN&ceid=IN:en"
            feed = feedparser.parse(google_url)
            filtered = feed.entries[:5]
            source_used = "Google News (headlines only)"

        if not filtered:
            return f"Data unavailable: No news found for {company_name}."

        news_str = f"Latest News for {company_name} (Source: {source_used}):\n\n"

        for i, entry in enumerate(filtered[:3]):
            title = entry.get('title', 'No title')
            link = entry.get('link', '')
            
            # Fetch full article text for Mint URLs
            if 'livemint.com' in link:
                article_text = fetch_article_text(link)
            else:
                # Google News fallback - headlines only
                summary_html = entry.get('summary', 'No summary available')
                soup = BeautifulSoup(summary_html, 'html.parser')
                article_text = soup.get_text(separator=' ', strip=True)
                article_text = f"Headline only - full text unavailable. {article_text}"

            news_str += f"{i+1}. {title}\n"
            news_str += f"   URL: {link}\n"
            news_str += f"   Content: {article_text[:200]}\n\n"

        return news_str

    except Exception as e:
        return f"Data unavailable: Failed to fetch news for {company_name}. ({e})"

def fetch_financials(company_name: str) -> str:
    """
    Fetches financial data from Screener.in by searching for the company.
    Scrapes key metrics like revenue, profit, debt, PE ratio using requests and BeautifulSoup.
    Returns a formatted financial snapshot string.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Step 1: Search for the company on Screener.in API
        search_url = "https://www.screener.in/api/company/search/"
        search_response = requests.get(search_url, params={'q': company_name}, headers=headers, timeout=10)
        search_response.raise_for_status()
        
        search_results = search_response.json()
        if not search_results:
            return f"Data unavailable: No financial data found on Screener.in for {company_name}."
            
        company_path = search_results[0].get('url')
        if not company_path:
            return f"Data unavailable: Could not determine Screener URL for {company_name}."
            
        # Step 2: Fetch the company's specific page
        company_url = f"https://www.screener.in{company_path}"
        page_response = requests.get(company_url, headers=headers, timeout=10)
        page_response.raise_for_status()
        
        # Step 3: Parse the HTML and extract key metrics
        soup = BeautifulSoup(page_response.text, 'html.parser')
        
        # Screener.in stores key metrics in a 'company-ratios' section (often under a ul tag with id='top-ratios')
        ratios_section = soup.find('ul', id='top-ratios')
        if not ratios_section:
            # Fallback if id is not found
            ratios_section = soup.find('div', class_='company-ratios')
            
        if not ratios_section:
            return f"Data unavailable: Key metrics section not found on Screener.in for {company_name}."
            
        ratios = ratios_section.find_all('li')
        financials_str = f"Financial Snapshot for {company_name} (Screener.in):\n\n"
        
        for ratio in ratios:
            name_span = ratio.find('span', class_='name')
            nowrap_span = ratio.find('span', class_='nowrap') # Typically contains the number and unit
            
            if name_span and nowrap_span:
                name_text = name_span.get_text(strip=True)
                val_text = nowrap_span.get_text(separator=' ', strip=True).replace('₹', 'Rs.')
                financials_str += f"- {name_text}: {val_text}\n"
                
        if len(financials_str) > 1000:
            financials_str = financials_str[:1000] + "... [truncated]"
            
        return financials_str
    except Exception as e:
        # Handle errors gracefully as requested
        return f"Data unavailable: Failed to fetch financial data for {company_name}. ({e})"

def get_company_domain(company_name: str) -> str:
    domain_mapping = {
        "zomato": "zomato.com",
        "paytm": "paytm.com",
        "swiggy": "swiggy.com",
        "infosys": "infosys.com",
        "jio financial": "jio.com",
        "tcs": "tcs.com",
        "wipro": "wipro.com",
        "reliance": "ril.com",
        "hdfc": "hdfcbank.com",
        "icici": "icicibank.com"
    }
    return domain_mapping.get(company_name.lower().strip(), "")


# --- PARSER FUNCTIONS FOR STRUCTURE EXTRACTION ---

def parse_waterfall(text: str) -> dict:
    """Extract waterfall data from WATERFALL: label: $X | label: -$X format."""
    from collections import OrderedDict
    pattern = r"WATERFALL:\s*(.*?)(?:\n|$)"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return OrderedDict()
    
    items = match.group(1).split("|")
    result = OrderedDict()
    try:
        for item in items:
            parts = item.strip().split(":")
            if len(parts) == 2:
                label = parts[0].strip()
                value_str = parts[1].strip().replace("$", "").replace(",", "")
                result[label] = float(value_str)
    except Exception:
        pass
    
    return result


def parse_pullquote(text: str) -> str:
    """Extract PULLQUOTE text."""
    pattern = r"PULLQUOTE:\s*(.*?)(?:\n|$)"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def parse_risk_register(text: str) -> list:
    """Extract Risk Register data with Likelihood x Impact format."""
    risks = []
    risk_pattern = r"Risk:\s*([^\n]+)\n.*?Likelihood x Impact:\s*(\w+)\s*x\s*(\w+)\n.*?Mitigation & Owner:\s*([^\n]+)\s*\(Owner:\s*([^\n)]+)\)"
    
    for match in re.finditer(risk_pattern, text, re.IGNORECASE | re.DOTALL):
        risk_dict = {
            "name": match.group(1).strip(),
            "likelihood": match.group(2).strip(),
            "impact": match.group(3).strip(),
            "mitigation": match.group(4).strip(),
            "owner": match.group(5).strip(),
        }
        risks.append(risk_dict)
    
    return risks


# --- CHART GENERATION FUNCTIONS ---

def generate_waterfall_chart(waterfall_data: dict, company_name: str,
                              headline: str, timestamp: str) -> str:
    """Generate McKinsey-style waterfall chart."""
    if not waterfall_data:
        return ""
    
    try:
        labels = list(waterfall_data.keys())
        values = list(waterfall_data.values())
        
        cumulative = 0
        starts = []
        for i, val in enumerate(values):
            if i == 0 or i == len(values) - 1:
                starts.append(0)
            else:
                starts.append(cumulative)
                cumulative += val
        
        colors = [MCKINSEY_BLUE if (i == 0 or i == len(values) - 1 or values[i] > 0)
                  else MCKINSEY_GRAY for i in range(len(values))]
        
        fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
        ax.bar(range(len(labels)), values, bottom=starts, color=colors, edgecolor='black', linewidth=1)
        
        for i, (label, val) in enumerate(zip(labels, values)):
            y_pos = starts[i] + val / 2
            ax.text(i, y_pos, f"${abs(val):.0f}", ha='center', va='center',
                   fontweight='bold', fontsize=9, color='white' if abs(val) > 50 else 'black')
        
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=9)
        ax.set_ylabel("Amount ($)", fontsize=9, color=MCKINSEY_GRAY)
        ax.set_title(headline, fontsize=11, fontweight='bold', color=MCKINSEY_DARK)
        apply_mckinsey_style(ax)
        
        os.makedirs("output", exist_ok=True)
        safe_company = "".join(c if c.isalnum() else "_" for c in company_name)
        chart_path = os.path.join("output", f"waterfall_{safe_company}_{timestamp}.png")
        plt.tight_layout()
        plt.savefig(chart_path, bbox_inches='tight', dpi=150)
        plt.close()
        return chart_path
    except Exception as e:
        print(f"Error generating waterfall chart: {e}")
        return ""


def generate_options_radar_chart(option_scores: dict, company_name: str,
                                  timestamp: str) -> str:
    """Generate radar chart comparing strategic options."""
    try:
        criteria = ["P&L", "Feasibility", "CustomerRisk", "Speed", "OpComplexity", "CompDefense", "RegRisk"]
        options = list(option_scores.keys())[:3]
        
        angles = np.linspace(0, 2 * np.pi, len(criteria), endpoint=False).tolist()
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'), dpi=150)
        
        colors_radar = [MCKINSEY_BLUE, MCKINSEY_AMBER, MCKINSEY_GREEN]
        for idx, option in enumerate(options):
            scores = []
            for crit in criteria:
                score = option_scores[option].get(crit, 3.0)
                scores.append(float(score))
            scores += scores[:1]
            
            ax.plot(angles, scores, 'o-', linewidth=2, label=option, color=colors_radar[idx])
            ax.fill(angles, scores, alpha=0.15, color=colors_radar[idx])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(criteria, fontsize=9, color=MCKINSEY_GRAY)
        ax.set_ylim(0, 5)
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_yticklabels(['1', '2', '3', '4', '5'], fontsize=8, color=MCKINSEY_GRAY)
        ax.grid(True, color='#e5e7eb', linestyle='-', linewidth=0.5)
        ax.set_title(f"Strategic Options Comparison — {company_name}", 
                    fontsize=11, fontweight='bold', color=MCKINSEY_DARK, pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)
        
        os.makedirs("output", exist_ok=True)
        safe_company = "".join(c if c.isalnum() else "_" for c in company_name)
        chart_path = os.path.join("output", f"radar_{safe_company}_{timestamp}.png")
        plt.tight_layout()
        plt.savefig(chart_path, bbox_inches='tight', dpi=150)
        plt.close()
        return chart_path
    except Exception as e:
        print(f"Error generating radar chart: {e}")
        return ""


def generate_risk_matrix_chart(risks: list, company_name: str, timestamp: str) -> str:
    """Generate 2x2 risk matrix scatter plot."""
    try:
        likelihood_map = {"Low": 1, "Medium": 2, "High": 3}
        impact_map = {"Low": 1, "Medium": 2, "High": 3}
        
        fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
        
        for risk in risks:
            x = likelihood_map.get(risk.get("likelihood", "Medium"), 2)
            y = impact_map.get(risk.get("impact", "Medium"), 2)
            
            if x == 3 and y == 3:
                color = MCKINSEY_RED
            elif x >= 2 or y >= 2:
                color = MCKINSEY_AMBER
            else:
                color = MCKINSEY_GREEN
            
            ax.scatter(x, y, s=300, alpha=0.6, color=color, edgecolors='black', linewidth=1)
            ax.annotate(risk.get("name", "Risk"), (x, y), fontsize=8, ha='center', va='center')
        
        ax.set_xlim(0.5, 3.5)
        ax.set_ylim(0.5, 3.5)
        ax.set_xticks([1, 2, 3])
        ax.set_xticklabels(['Low', 'Medium', 'High'], fontsize=10, color=MCKINSEY_GRAY)
        ax.set_yticks([1, 2, 3])
        ax.set_yticklabels(['Low', 'Medium', 'High'], fontsize=10, color=MCKINSEY_GRAY)
        ax.set_xlabel("Likelihood", fontsize=10, fontweight='bold', color=MCKINSEY_GRAY)
        ax.set_ylabel("Impact", fontsize=10, fontweight='bold', color=MCKINSEY_GRAY)
        ax.set_title(f"{company_name} — Risk Register", fontsize=11, fontweight='bold', color=MCKINSEY_DARK)
        ax.grid(True, color='#e5e7eb', linestyle='--', linewidth=0.5, alpha=0.5)
        apply_mckinsey_style(ax)
        
        os.makedirs("output", exist_ok=True)
        safe_company = "".join(c if c.isalnum() else "_" for c in company_name)
        chart_path = os.path.join("output", f"risk_matrix_{safe_company}_{timestamp}.png")
        plt.tight_layout()
        plt.savefig(chart_path, bbox_inches='tight', dpi=150)
        plt.close()
        return chart_path
    except Exception as e:
        print(f"Error generating risk matrix: {e}")
        return ""


def generate_monte_carlo_summary_chart(win_probs: dict, robustness: dict,
                                        company_name: str, timestamp: str) -> str:
    """Generate Monte Carlo summary chart with robustness thresholds."""
    try:
        sorted_options = sorted(win_probs.items(), key=lambda x: x[1])
        names = [x[0] for x in sorted_options]
        probs = [x[1] for x in sorted_options]
        
        colors = []
        for prob in probs:
            if prob >= 70:
                colors.append(MCKINSEY_BLUE)
            elif prob >= 50:
                colors.append(MCKINSEY_AMBER)
            else:
                colors.append(MCKINSEY_GRAY)
        
        fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
        bars = ax.barh(names, probs, color=colors, edgecolor='black', linewidth=1)
        
        ax.axvline(x=70, color=MCKINSEY_RED, linestyle='--', linewidth=2, alpha=0.7, label='Highly Robust (70%)')
        ax.axvline(x=50, color=MCKINSEY_AMBER, linestyle='--', linewidth=1.5, alpha=0.5, label='Moderately Robust (50%)')
        
        for i, prob in enumerate(probs):
            ax.text(prob + 2, i, f"{prob:.1f}%", va='center', fontsize=9, fontweight='bold')
        
        ax.set_xlim(0, 100)
        ax.set_xlabel("Win Probability (%)", fontsize=10, fontweight='bold', color=MCKINSEY_GRAY)
        ax.set_title(f"Monte Carlo Robustness Test — {company_name}", 
                    fontsize=11, fontweight='bold', color=MCKINSEY_DARK)
        ax.legend(loc='lower right', fontsize=8)
        apply_mckinsey_style(ax)
        
        os.makedirs("output", exist_ok=True)
        safe_company = "".join(c if c.isalnum() else "_" for c in company_name)
        chart_path = os.path.join("output", f"monte_carlo_summary_{safe_company}_{timestamp}.png")
        plt.tight_layout()
        plt.savefig(chart_path, bbox_inches='tight', dpi=150)
        plt.close()
        return chart_path
    except Exception as e:
        print(f"Error generating Monte Carlo summary: {e}")
        return ""


# --- Archetype weight tables (sum to 100%) ---
CUSTOMER_INTIMACY_WEIGHTS = {
    "P&L_Impact": 25,
    "Customer_Market_Risk": 28,
    "Speed_to_Impact": 15,
    "Competitive_Defensibility": 12,
    "Implementation_Feasibility": 10,
    "Operational_Complexity": 6,
    "Regulatory_External_Risk": 4,
}

OPERATIONAL_EXCELLENCE_WEIGHTS = {
    "P&L_Impact": 28,
    "Implementation_Feasibility": 20,
    "Operational_Complexity": 18,
    "Customer_Market_Risk": 12,
    "Speed_to_Impact": 10,
    "Competitive_Defensibility": 8,
    "Regulatory_External_Risk": 4,
}

PRODUCT_LEADERSHIP_WEIGHTS = {
    "P&L_Impact": 25,
    "Competitive_Defensibility": 22,
    "Customer_Market_Risk": 18,
    "Regulatory_External_Risk": 12,
    "Implementation_Feasibility": 10,
    "Speed_to_Impact": 8,
    "Operational_Complexity": 5,
}

FINANCIAL_SERVICES_WEIGHTS = {
    "P&L_Impact": 20,
    "Regulatory_External_Risk": 28,
    "Implementation_Feasibility": 18,
    "Customer_Market_Risk": 14,
    "Competitive_Defensibility": 10,
    "Speed_to_Impact": 6,
    "Operational_Complexity": 4,
}

HUMAN_CAPITAL_WEIGHTS = {
    "P&L_Impact": 22,
    "Competitive_Defensibility": 25,
    "Customer_Market_Risk": 15,
    "Implementation_Feasibility": 14,
    "Regulatory_External_Risk": 12,
    "Speed_to_Impact": 8,
    "Operational_Complexity": 4,
}

INDUSTRIAL_CAPITAL_WEIGHTS = {
    "P&L_Impact": 30,
    "Implementation_Feasibility": 22,
    "Operational_Complexity": 18,
    "Regulatory_External_Risk": 12,
    "Customer_Market_Risk": 8,
    "Speed_to_Impact": 6,
    "Competitive_Defensibility": 4,
}

ARCHETYPE_DIMENSIONS = [
    ("Operations_Intensity", OPERATIONAL_EXCELLENCE_WEIGHTS, "Operational Excellence", "Treacy & Wiersema: Operational Excellence"),
    ("Technology_Platform_Intensity", PRODUCT_LEADERSHIP_WEIGHTS, "Product Leadership", "Treacy & Wiersema: Product Leadership / BCG Adaptive Advantage"),
    ("Consumer_Brand_Intensity", CUSTOMER_INTIMACY_WEIGHTS, "Customer Intimacy", "Treacy & Wiersema: Customer Intimacy"),
    ("Financial_Services_Intensity", FINANCIAL_SERVICES_WEIGHTS, "Financial Services", "Damodaran sector risk framework"),
    ("Industrial_Capital_Intensity", INDUSTRIAL_CAPITAL_WEIGHTS, "Industrial Capital", "Porter: capital barriers to entry"),
    ("Human_Intangible_Capital_Intensity", HUMAN_CAPITAL_WEIGHTS, "Human Capital", "Kaplan & Norton BSC: Learning & Growth"),
]

_CLASSIFICATION_BLOCK_RE = re.compile(
    r"COMPANY_CLASSIFICATION:\s*\n?"
    r"Operations:\s*(\d+(?:\.\d+)?)\s*\|\s*Technology:\s*(\d+(?:\.\d+)?)\s*\|\s*"
    r"ConsumerBrand:\s*(\d+(?:\.\d+)?)\s*\|\s*Financial:\s*(\d+(?:\.\d+)?)\s*\|\s*"
    r"Industrial:\s*(\d+(?:\.\d+)?)\s*\|\s*Competitive:\s*(\d+(?:\.\d+)?)\s*\|\s*"
    r"HumanCapital:\s*(\d+(?:\.\d+)?)\s*\|\s*Regulatory:\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def _clamp_score(value: float) -> float:
    return max(0.0, min(10.0, float(value)))


def _normalize_weights(weights: dict) -> dict:
    total = sum(weights.values())
    if total <= 0:
        n = len(weights)
        return {k: 100.0 / n for k in weights}
    return {k: (v / total) * 100.0 for k, v in weights.items()}


def _blend_weight_tables(primary: dict, secondary: dict, primary_share: float = 0.70) -> dict:
    all_keys = set(primary) | set(secondary)
    blended = {}
    for key in all_keys:
        blended[key] = primary.get(key, 0) * primary_share + secondary.get(key, 0) * (1 - primary_share)
    return _normalize_weights(blended)


def _score_dimension(text: str, keywords: list, base: float = 3.0, per_hit: float = 1.2) -> float:
    lower = text.lower()
    hits = sum(1 for kw in keywords if kw in lower)
    return _clamp_score(base + hits * per_hit)


def classify_company(text: str) -> dict:
    """
    Parse or infer 0-10 scores on 8 company classification dimensions.
    """
    block_match = _CLASSIFICATION_BLOCK_RE.search(text)
    if block_match:
        return {
            "Operations_Intensity": _clamp_score(block_match.group(1)),
            "Technology_Platform_Intensity": _clamp_score(block_match.group(2)),
            "Consumer_Brand_Intensity": _clamp_score(block_match.group(3)),
            "Financial_Services_Intensity": _clamp_score(block_match.group(4)),
            "Industrial_Capital_Intensity": _clamp_score(block_match.group(5)),
            "Competitive_Market_Intensity": _clamp_score(block_match.group(6)),
            "Human_Intangible_Capital_Intensity": _clamp_score(block_match.group(7)),
            "Regulatory_Policy_Intensity": _clamp_score(block_match.group(8)),
        }

    lower = text.lower()
    return {
        "Operations_Intensity": _score_dimension(
            lower,
            ["logistics", "supply chain", "delivery", "warehouse", "manufacturing", "operations", "distribution"],
        ),
        "Technology_Platform_Intensity": _score_dimension(
            lower,
            ["platform", "app", "software", "r&d", "data", "network effect", "digital", "technology", "saas"],
        ),
        "Consumer_Brand_Intensity": _score_dimension(
            lower,
            ["b2c", "brand", "consumer", "loyalty", "retail", "jewellery", "jewelry", "emotional", "customer experience"],
        ),
        "Financial_Services_Intensity": _score_dimension(
            lower,
            ["rbi", "sebi", "lending", "bank", "nbfc", "insurance", "capital requirement", "regulatory capital", "financial services"],
            base=2.0,
            per_hit=1.5,
        ),
        "Industrial_Capital_Intensity": _score_dimension(
            lower,
            ["capex", "infrastructure", "plant", "factory", "heavy asset", "capital intensive", "industrial"],
        ),
        "Competitive_Market_Intensity": _score_dimension(
            lower,
            ["competitor", "rivalry", "market share", "price war", "fragmented", "competition", "low switching"],
        ),
        "Human_Intangible_Capital_Intensity": _score_dimension(
            lower,
            ["talent", "ip", "patent", "intellectual property", "skilled", "human capital", "r&d spend"],
        ),
        "Regulatory_Policy_Intensity": _score_dimension(
            lower,
            ["compliance", "government", "policy", "regulation", "pricing control", "regulatory"],
        ),
    }


def derive_baseline_weights(classification: dict) -> dict:
    """
    Derive criterion weights from classification using dominant-logic archetype rules.
    """
    scores = {
        dim: classification.get(dim, 0)
        for dim, _, _, _ in ARCHETYPE_DIMENSIONS
    }

    if classification.get("Financial_Services_Intensity", 0) > 7:
        return {
            "weights": dict(FINANCIAL_SERVICES_WEIGHTS),
            "archetype": "Financial Services",
            "classification_type": "Pure",
            "academic_basis": "Damodaran sector risk framework (financial services override)",
        }

    ranked = sorted(
        [(dim, scores[dim], weights, name, basis) for dim, weights, name, basis in ARCHETYPE_DIMENSIONS],
        key=lambda x: x[1],
        reverse=True,
    )
    dominant = ranked[0]
    secondary = ranked[1]
    gap = dominant[1] - secondary[1]

    if gap > 2:
        classification_type = "Pure"
        final_weights = dict(dominant[2])
        academic_basis = dominant[4]
    else:
        classification_type = "Hybrid"
        final_weights = _blend_weight_tables(dominant[2], secondary[2], 0.70)
        academic_basis = (
            f"Prahalad & Bettis dominant logic (hybrid): {dominant[3]} + {secondary[3]}"
        )

    archetype = dominant[3]
    if classification_type == "Hybrid":
        archetype = f"{dominant[3]} + {secondary[3]}"

    return {
        "weights": _normalize_weights(final_weights),
        "archetype": archetype,
        "classification_type": classification_type,
        "academic_basis": academic_basis,
    }


def detect_problem_parameters(
    problem: str,
    base_weights: dict,
    classification_type: str,
) -> dict:
    """
    Calibrate weights based on problem-statement keywords.
    """
    problem_lower = problem.lower()
    weights = dict(base_weights.get("weights", base_weights))
    parameters_added = []

    keyword_rules = [
        (
            ("fuel", "cost", "operations", "logistics", "supply"),
            "Operational_Cost_Sensitivity",
            8,
            "Operational_Complexity",
            4,
        ),
        (
            ("market entry", "expansion", "new market", "geographic"),
            "Market_Entry_Barrier",
            10,
            "Regulatory_External_Risk",
            3,
        ),
        (
            ("technology", "digital", "ai", "automation", "tech"),
            "Technology_Access",
            8,
            "Operational_Complexity",
            3,
        ),
        (
            ("consumer", "sentiment", "trust", "brand", "reputation"),
            "Consumer_Sentiment_Index",
            10,
            "Speed_to_Impact",
            4,
        ),
        (
            ("profitability", "losses", "margins", "ebitda", "costs", "revenue"),
            "Cash_Burn_Sensitivity",
            12,
            "Customer_Market_Risk",
            4,
        ),
        (
            ("competition", "competitor", "market share", "rivalry"),
            "Competitive_Response_Speed",
            8,
            "Implementation_Feasibility",
            3,
        ),
        (
            ("regulation", "compliance", "government", "policy", "rbi", "sebi"),
            "Regulatory_Compliance_Cost",
            12,
            "Speed_to_Impact",
            5,
        ),
    ]

    for keywords, param_name, add_pct, reduce_key, reduce_pct in keyword_rules:
        if any(kw in problem_lower for kw in keywords):
            weights[param_name] = weights.get(param_name, 0) + add_pct
            weights[reduce_key] = max(0, weights.get(reduce_key, 0) - reduce_pct)
            parameters_added.append(param_name)

    final_weights = _normalize_weights(weights)
    archetype = base_weights.get("archetype", "Unknown")
    cal_type = classification_type or base_weights.get("classification_type", "Unknown")
    calibration_report = (
        f"Base archetype: {archetype}\n"
        f"Classification: {cal_type}\n"
        f"Parameters added: {parameters_added}\n"
        f"Final weights: {final_weights}"
    )

    return {
        "final_weights": final_weights,
        "parameters_added": parameters_added,
        "calibration_report": calibration_report,
        "archetype": archetype,
        "classification_type": cal_type,
    }


MONTE_CARLO_VARIATION_RANGES = {
    "Regulatory_External_Risk": 0.15,
    "Regulatory_Compliance_Cost": 0.15,
    "Operational_Cost_Sensitivity": 0.15,
    "P&L_Impact": 0.30,
    "Implementation_Feasibility": 0.30,
    "Operational_Complexity": 0.30,
    "Customer_Market_Risk": 0.45,
    "Consumer_Sentiment_Index": 0.45,
    "Competitive_Defensibility": 0.45,
    "Competitive_Response_Speed": 0.45,
    "Market_Entry_Barrier": 0.45,
    "Speed_to_Impact": 0.40,
    "Technology_Access": 0.35,
    "Cash_Burn_Sensitivity": 0.35,
}

OPTION_SCORE_CRITERION_MAP = {
    "P&L": "P&L_Impact",
    "P&L_Impact": "P&L_Impact",
    "Feasibility": "Implementation_Feasibility",
    "Implementation_Feasibility": "Implementation_Feasibility",
    "CustomerRisk": "Customer_Market_Risk",
    "Customer_Market_Risk": "Customer_Market_Risk",
    "Speed": "Speed_to_Impact",
    "Speed_to_Impact": "Speed_to_Impact",
    "OpComplexity": "Operational_Complexity",
    "Operational_Complexity": "Operational_Complexity",
    "CompDefense": "Competitive_Defensibility",
    "Competitive_Defensibility": "Competitive_Defensibility",
    "RegRisk": "Regulatory_External_Risk",
    "Regulatory_External_Risk": "Regulatory_External_Risk",
}


def _map_option_scores_to_criteria(options_scores: dict) -> dict:
    mapped = {}
    for option_name, scores in options_scores.items():
        mapped[option_name] = {}
        for key, value in scores.items():
            criterion = OPTION_SCORE_CRITERION_MAP.get(key, key)
            mapped[option_name][criterion] = float(value)
    return mapped


def run_monte_carlo_options(
    options_scores: dict,
    calibrated_weights: dict,
    classification_type: str,
    n_simulations: int = 10000,
    company_name: str = "",
    problem: str = "",
    financial_override: bool = False,
) -> dict:
    """
    Monte Carlo simulation over weight uncertainty to rank strategic options.
    """
    weights = calibrated_weights.get("final_weights", calibrated_weights)
    if isinstance(calibrated_weights, dict) and "weights" in calibrated_weights and "final_weights" not in calibrated_weights:
        weights = calibrated_weights["weights"]

    mapped_options = _map_option_scores_to_criteria(options_scores)
    option_names = list(mapped_options.keys())
    if not option_names:
        return {
            "win_probabilities": {},
            "robustness_ratings": {},
            "recommended_option": None,
            "chart_filepath": "",
            "simulation_count": n_simulations,
        }

    criteria = list(weights.keys())
    company_multiplier = 0.85 if classification_type == "Pure" else 1.15

    regulatory_keys = {
        "Regulatory_External_Risk",
        "Regulatory_Compliance_Cost",
    }

    win_counts = {name: 0 for name in option_names}
    weight_vectors = np.array([weights.get(c, 0) for c in criteria], dtype=float)

    for _ in range(n_simulations):
        drawn = np.zeros(len(criteria))
        for i, criterion in enumerate(criteria):
            base_w = weight_vectors[i]
            base_range = MONTE_CARLO_VARIATION_RANGES.get(criterion, 0.25) * company_multiplier
            if financial_override:
                base_range *= 0.6 if criterion in regulatory_keys else 1.2
            low = max(0.0, base_w * (1 - base_range))
            high = base_w * (1 + base_range)
            drawn[i] = np.random.uniform(low, high if high > low else low + 0.01)

        if drawn.sum() <= 0:
            drawn = np.ones(len(criteria))
        drawn = drawn / drawn.sum() * 100.0

        best_option = None
        best_score = -1.0
        for option_name, scores in mapped_options.items():
            total = 0.0
            for i, criterion in enumerate(criteria):
                option_val = scores.get(criterion, 3.0)
                total += drawn[i] * option_val
            if total > best_score:
                best_score = total
                best_option = option_name

        if best_option:
            win_counts[best_option] += 1

    win_probabilities = {
        name: (win_counts[name] / n_simulations) * 100.0 for name in option_names
    }

    robustness_ratings = {}
    for name, prob in win_probabilities.items():
        if prob >= 70:
            robustness_ratings[name] = "Highly Robust"
        elif prob >= 50:
            robustness_ratings[name] = "Moderately Robust"
        else:
            robustness_ratings[name] = "Sensitive to assumptions"

    recommended_option = max(win_probabilities, key=win_probabilities.get)

    os.makedirs("output", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_company = "".join(c if c.isalnum() else "_" for c in company_name) or "company"
    chart_filepath = os.path.join("output", f"monte_carlo_{safe_company}_{timestamp}.png")

    sorted_options = sorted(win_probabilities.items(), key=lambda x: x[1])
    names = [x[0] for x in sorted_options]
    probs = [x[1] for x in sorted_options]
    colors = []
    for prob in probs:
        if prob >= 70:
            colors.append("#22c55e")
        elif prob >= 50:
            colors.append("#f97316")
        else:
            colors.append("#ef4444")

    fig, ax = plt.subplots(figsize=(8, max(3, len(names) * 0.6)))
    ax.barh(names, probs, color=colors)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Win Probability (%)")
    ax.set_ylabel("Option")
    title_company = company_name or "Company"
    title_problem = problem or "Strategic Problem"
    ax.set_title(f"Monte Carlo Results — {title_company} — {title_problem}")
    plt.tight_layout()
    plt.savefig(chart_filepath, bbox_inches="tight")
    plt.close()

    base_case_scores = _compute_base_case_scores(mapped_options, weights, criteria)

    return {
        "win_probabilities": win_probabilities,
        "robustness_ratings": robustness_ratings,
        "recommended_option": recommended_option,
        "chart_filepath": chart_filepath,
        "simulation_count": n_simulations,
        "base_case_scores": base_case_scores,
        "mapped_options": mapped_options,
        "calibrated_weights": weights,
    }


CRITERION_LABELS = {
    "P&L_Impact": "P&L Impact",
    "Customer_Market_Risk": "Customer / Market Risk",
    "Speed_to_Impact": "Speed to Impact",
    "Competitive_Defensibility": "Competitive Defensibility",
    "Implementation_Feasibility": "Implementation Feasibility",
    "Operational_Complexity": "Operational Complexity",
    "Regulatory_External_Risk": "Regulatory / External Risk",
    "Operational_Cost_Sensitivity": "Operational Cost Sensitivity",
    "Market_Entry_Barrier": "Market Entry Barrier",
    "Technology_Access": "Technology Access",
    "Consumer_Sentiment_Index": "Consumer Sentiment Index",
    "Cash_Burn_Sensitivity": "Cash Burn / Revenue Sensitivity",
    "Regulatory_Compliance_Cost": "Regulatory Compliance Cost",
    "Competitive_Response_Speed": "Competitive Response Speed",
}


def _label_criterion(name: str) -> str:
    return CRITERION_LABELS.get(name, name.replace("_", " "))


def _compute_base_case_scores(
    mapped_options: dict, weights: dict, criteria: list
) -> dict:
    scores = {}
    for option_name, option_scores in mapped_options.items():
        total = 0.0
        for criterion in criteria:
            w = weights.get(criterion, 0) / 100.0
            total += w * option_scores.get(criterion, 3.0)
        scores[option_name] = round(total, 2)
    return scores


def _generate_calibrated_weights_chart(
    weights: dict, company_name: str, problem: str, safe_company: str, timestamp: str
) -> str:
    sorted_items = sorted(weights.items(), key=lambda x: x[1])
    labels = [_label_criterion(k) for k, _ in sorted_items]
    values = [v for _, v in sorted_items]

    fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.45)))
    ax.barh(labels, values, color="#4F46E5")
    ax.set_xlim(0, max(values) * 1.15 if values else 100)
    ax.set_xlabel("Weight (%)")
    ax.set_title(f"Calibrated Decision Criteria — {company_name}")
    fig.text(0.5, 0.01, f"Problem: {problem[:80]}{'...' if len(problem) > 80 else ''}",
             ha="center", fontsize=8, style="italic")
    plt.tight_layout()
    path = os.path.join("output", f"weights_{safe_company}_{timestamp}.png")
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


def _generate_option_comparison_chart(
    base_case_scores: dict, company_name: str, problem: str, safe_company: str, timestamp: str
) -> str:
    sorted_items = sorted(base_case_scores.items(), key=lambda x: x[1])
    names = [x[0] for x in sorted_items]
    scores = [x[1] for x in sorted_items]
    max_score = max(scores) if scores else 5
    colors = ["#22c55e" if s == max_score else "#94a3b8" for s in scores]

    fig, ax = plt.subplots(figsize=(8, max(3, len(names) * 0.55)))
    ax.barh(names, scores, color=colors)
    ax.set_xlim(0, 5.5)
    ax.set_xlabel("Weighted Score (1–5 scale)")
    ax.set_title(f"Base-Case Weighted Option Scores — {company_name}")
    ax.axvline(x=max_score, color="#16a34a", linestyle="--", alpha=0.5, label="Leader")
    plt.tight_layout()
    path = os.path.join("output", f"option_scores_{safe_company}_{timestamp}.png")
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


def _explain_monte_carlo_recommendation(
    monte_carlo: dict,
    calibration: dict,
    base_weights: dict,
    classification: dict,
    company_name: str,
    problem: str,
) -> str:
    weights = monte_carlo.get("calibrated_weights", calibration.get("final_weights", {}))
    base_case = monte_carlo.get("base_case_scores", {})
    recommended = monte_carlo.get("recommended_option", "N/A")
    win_probs = monte_carlo.get("win_probabilities", {})
    top_criteria = sorted(weights.items(), key=lambda x: -x[1])[:3]

    lines = [
        "Under the calibrated base-case weights (before Monte Carlo perturbation), "
        "options rank as follows:"
    ]
    for name, score in sorted(base_case.items(), key=lambda x: -x[1]):
        lines.append(f"- {name}: {score:.2f} / 5.00")

    driver_text = ", ".join(
        f"{_label_criterion(c)} ({w:.1f}%)" for c, w in top_criteria
    )
    rec_prob = win_probs.get(recommended, 0)
    archetype = base_weights.get("archetype", calibration.get("archetype", "Unknown"))
    cal_type = base_weights.get("classification_type", calibration.get("classification_type", ""))
    params = calibration.get("parameters_added", [])

    explanation = (
        f"The Monte Carlo simulation recommends {recommended}, which prevailed in "
        f"{rec_prob:.1f}% of {monte_carlo.get('simulation_count', 10000):,} trials. "
        f"This outcome is driven primarily by {driver_text} — the three highest-weight "
        f"criteria after calibrating for a **{archetype}** ({cal_type}) company profile."
    )
    if params:
        param_labels = ", ".join(_label_criterion(p) for p in params)
        explanation += (
            f" Problem-specific calibration elevated {param_labels} because the "
            f"stated challenge ('{problem}') signals heightened sensitivity in those areas."
        )
    explanation += (
        f" For {company_name}, a {cal_type.lower()} classification applies "
        f"{'tighter' if cal_type == 'Pure' else 'wider'} weight uncertainty bands "
        f"({'±15%' if cal_type == 'Hybrid' else '±12%'} effective range on key criteria), "
        f"which is why robustness ratings should be read alongside the narrative recommendation."
    )

    if classification:
        top_dims = sorted(
            [
                (k, v)
                for k, v in classification.items()
                if k.endswith("_Intensity")
            ],
            key=lambda x: -x[1],
        )[:2]
        if top_dims:
            dim_names = [k.replace("_Intensity", "").replace("_", " ") for k, _ in top_dims]
            explanation += (
                f" Classification signals ({dim_names[0]}: {top_dims[0][1]:.0f}/10"
                + (f", {dim_names[1]}: {top_dims[1][1]:.0f}/10" if len(top_dims) > 1 else "")
                + ") shaped the archetype weights used in this analysis."
            )

    lines.append("")
    lines.append(explanation)
    return "\n".join(lines)


def format_analytics_appendix(
    company_name: str,
    problem: str,
    classification: dict,
    base_weights: dict,
    calibration: dict,
    monte_carlo: dict,
) -> tuple:
    """
    Build consulting-style analytics appendix text and supporting chart paths.
    Works for any company and problem statement.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_company = "".join(c if c.isalnum() else "_" for c in company_name) or "company"
    weights = calibration.get("final_weights", {})
    archetype = base_weights.get("archetype", "Unknown")
    cal_type = base_weights.get("classification_type", "Unknown")
    academic = base_weights.get("academic_basis", "")
    params = calibration.get("parameters_added", [])

    chart_paths = []
    if monte_carlo.get("chart_filepath"):
        chart_paths.append(monte_carlo["chart_filepath"])
    chart_paths.append(
        _generate_calibrated_weights_chart(weights, company_name, problem, safe_company, timestamp)
    )
    if monte_carlo.get("base_case_scores"):
        chart_paths.append(
            _generate_option_comparison_chart(
                monte_carlo["base_case_scores"], company_name, problem, safe_company, timestamp
            )
        )

    dim_lines = []
    if classification:
        dim_map = [
            ("Operations", "Operations_Intensity"),
            ("Technology", "Technology_Platform_Intensity"),
            ("Consumer Brand", "Consumer_Brand_Intensity"),
            ("Financial Services", "Financial_Services_Intensity"),
            ("Industrial Capital", "Industrial_Capital_Intensity"),
            ("Competitive Intensity", "Competitive_Market_Intensity"),
            ("Human Capital", "Human_Intangible_Capital_Intensity"),
            ("Regulatory", "Regulatory_Policy_Intensity"),
        ]
        for label, key in dim_map:
            if key in classification:
                dim_lines.append(f"- {label}: {classification[key]:.0f}/10")

    weight_lines = [
        f"- {_label_criterion(k)}: {v:.1f}%"
        for k, v in sorted(weights.items(), key=lambda x: -x[1])
    ]

    robust_lines = []
    for option_name, prob in sorted(
        monte_carlo.get("win_probabilities", {}).items(), key=lambda x: -x[1]
    ):
        rating = monte_carlo.get("robustness_ratings", {}).get(option_name, "")
        robust_lines.append(f"| {option_name} | {prob:.1f}% | {rating} |")

    reasoning = _explain_monte_carlo_recommendation(
        monte_carlo, calibration, base_weights, classification, company_name, problem
    )

    param_narrative = (
        "No problem-specific parameters were required; base archetype weights applied directly."
        if not params
        else (
            "The problem statement triggered additional calibration parameters: "
            + ", ".join(_label_criterion(p) for p in params)
            + ". These adjust the evaluation lens to reflect immediate strategic pressures "
            "beyond the company's structural archetype."
        )
    )

    appendix = f"""
---

## StratAgent Analytics Appendix

### 1. Company Classification & Strategic Profile
**Client:** {company_name}
**Problem under review:** {problem}

Our classification engine assessed {company_name} across eight structural dimensions (0-10 scale):
{chr(10).join(dim_lines) if dim_lines else "- Classification data drawn from analyst structured output."}

**Dominant logic:** {archetype} ({cal_type})
**Framework basis:** {academic}

### 2. Calibrated Evaluation Framework
The decision criteria below combine archetype-based weights with problem-specific calibration.
{param_narrative}

**Final criterion weights (sum = 100%):**
{chr(10).join(weight_lines)}

### 3. Base-Case Option Assessment
Before stress-testing weights, each option was scored on a 1-5 scale across seven core criteria
and weighted using the calibrated framework above.

{reasoning}

### 4. Monte Carlo Robustness Test
To test sensitivity to weighting assumptions, we ran **{monte_carlo.get('simulation_count', 10000):,}**
Monte Carlo simulations. In each trial, criterion weights were perturbed within academically
grounded ranges, re-normalized to 100%, and options re-ranked.

**Quantitative recommendation:** {monte_carlo.get('recommended_option', 'N/A')}

| Strategic Option | Win Probability | Robustness Assessment |
| --- | --- | --- |
{chr(10).join(robust_lines)}

**How to read this:** Options with win probability ≥70% are *Highly Robust* under weight uncertainty;
50–70% are *Moderately Robust*; below 50% are *Sensitive to assumptions* and should not be selected
on quantitative grounds alone without mitigating key risks.

### 5. Analytical Exhibits
The following charts support this appendix and are embedded in the saved PDF brief:
1. **Monte Carlo Win Probabilities** — distribution of winning option across simulated weight scenarios
2. **Calibrated Decision Criteria** — final weight allocation after archetype and problem calibration
3. **Base-Case Weighted Scores** — option ranking at central weight estimates (pre-simulation)

*Exhibit files saved under `output/` for this run.*
""".strip()

    return appendix, chart_paths


def save_brief(
    content: str,
    company_name: str,
    problem: str = "",
    analytics_charts: list = None,
    pullquote: str = "",
    risk_data: list = None,
) -> str:
    """
    Saves the final StratAgent brief as a clean McKinsey-style PDF.
    Strips all internal scaffolding tags and embeds multiple charts.
    """
    try:
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_company_name = "".join([c if c.isalnum() else "_" for c in company_name])
        filename = os.path.join("output", f"{safe_company_name}_brief_{timestamp}.pdf")
        
        # Extract metrics from content BEFORE cleaning
        print(f"Parsing metrics for: {company_name}")
        roce_val, roe_val, pe_val = "Data unavailable", "Data unavailable", "Data unavailable"
        metrics_pattern = re.compile(r"ROCE:\s*([^\n]+)\s*ROE:\s*([^\n]+)\s*PE:\s*([^\n]+)", re.IGNORECASE)
        match = metrics_pattern.search(content)
        
        def parse_financial_metric(val_str):
            if "unavailable" in val_str.lower():
                return "Data unavailable"
            clean = re.sub(r"[^\d.-]", "", val_str)
            try:
                return float(clean)
            except:
                return "Data unavailable"
                
        if match:
            roce_val = parse_financial_metric(match.group(1))
            roe_val = parse_financial_metric(match.group(2))
            pe_val = parse_financial_metric(match.group(3))
        
        # Clean content: strip out the METRICS FOR CHART block so it doesn't appear in the PDF
        content = re.sub(r"## METRICS FOR CHART.*", "", content, flags=re.IGNORECASE | re.DOTALL).strip()
        
        # Clean content: remove all internal tags
        content = clean_for_pdf(content)
            
        # 2. Generate Chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))
        metrics = ['ROCE', 'ROE', 'PE Ratio']
        values = []
        labels = []
        for v in [roce_val, roe_val, pe_val]:
            if isinstance(v, float):
                values.append(v)
                labels.append(str(round(v, 2)))
            else:
                values.append(0.0)
                labels.append("Data unavailable")
                
        # Plot 1: Returns (ROCE, ROE)
        bars1 = ax1.bar(['ROCE', 'ROE'], [values[0], values[1]], color=['#4F46E5', '#10B981'])
        ax1.set_title('Returns (%)')
        ax1.set_ylabel('Value (%)')
        for i, bar in enumerate(bars1):
            yval = bar.get_height()
            va = 'bottom' if yval >= 0 else 'top'
            offset = yval + (0.5 if yval >= 0 else -0.5)
            ax1.text(bar.get_x() + bar.get_width()/2, offset, labels[i], ha='center', va=va, fontsize=9)
            
        # Plot 2: Valuation (PE)
        bars2 = ax2.bar(['PE Ratio'], [values[2]], color=['#F59E0B'])
        ax2.set_title('Valuation')
        ax2.set_ylabel('Price-to-Earnings')
        for i, bar in enumerate(bars2):
            yval = bar.get_height()
            va = 'bottom' if yval >= 0 else 'top'
            offset = max(yval, 0.5) if yval >= 0 else min(yval, -0.5)
            ax2.text(bar.get_x() + bar.get_width()/2, offset, labels[2], ha='center', va=va, fontsize=9)
            
        fig.suptitle(f'Key Financial Metrics: {company_name}')
        plt.tight_layout()
        chart_path = os.path.join("output", f"{safe_company_name}_chart_{timestamp}.png")
        plt.savefig(chart_path, bbox_inches='tight')
        plt.close()
        
        # 3. Fetch Logo
        domain = get_company_domain(company_name)
        logo_path = None
        if domain:
            logo_url = f"https://logo.clearbit.com/{domain}"
            try:
                resp = requests.get(logo_url, timeout=5)
                if resp.status_code == 200:
                    logo_path = os.path.join("output", f"{safe_company_name}_logo.png")
                    with open(logo_path, "wb") as f:
                        f.write(resp.content)
            except Exception:
                pass
                
        # 4. Generate PDF
        pdf = StratAgentPDF()
        
        # --- COVER PAGE ---
        pdf.add_page()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        
        pdf.ln(40)
        
        if logo_path and os.path.exists(logo_path):
            # Center the logo. Width = 40, x = (210 - 40)/2 = 85
            pdf.image(logo_path, x=85, w=40)
            pdf.ln(40)
            
        pdf.set_font("Helvetica", style="B", size=24)
        pdf.cell(0, 10, "StratAgent Consulting Brief", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(10)
        
        pdf.set_font("Helvetica", style="B", size=32)
        pdf.cell(0, 15, company_name, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(20)
        
        pdf.set_font("Helvetica", style="I", size=16)
        pdf.multi_cell(0, 8, f"Problem Statement: {problem}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(20)
        
        pdf.set_font("Helvetica", size=12)
        formatted_date = datetime.datetime.now().strftime("%B %d, %Y")
        pdf.cell(0, 10, f"Generated on: {formatted_date}", new_x="LMARGIN", new_y="NEXT", align="C")
        
        # --- CONTENT PAGES ---
        pdf.add_page()
        
        # Process Content
        lines = content.split('\n')
        in_situation = False
        for line in lines:
            line = line.strip()
            if not line:
                pdf.ln(4)
                continue
            
            # Remove asterisks used for bolding in markdown
            line = line.replace('**', '')
            
            # Handle headers
            if line.startswith('#'):
                # Strip # and ##
                clean_header = line.lstrip('#').strip()
                # Skip the title if the LLM repeats it as a header
                if clean_header.lower().startswith(f"stratagent brief:"):
                    continue
                    
                # If we just finished processing ## Situation block, embed the chart BEFORE the new header
                if in_situation and safe_header.lower() != "situation":
                    if os.path.exists(chart_path):
                        pdf.image(chart_path, x=25, w=160)
                        pdf.ln(10)
                    in_situation = False
                pdf.ln(4)
                # Replace commonly used unicode characters
                safe_header = clean_header.replace('—', '-').replace('–', '-').replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
                # FPDF2 handles utf-8 natively, but replacing smart quotes helps standard fonts
                if safe_header.lower().startswith("framework selected:"):
                    parts = safe_header.split(":", 1)
                    pdf.set_font("Helvetica", style="B", size=14)
                    pdf.write(8, parts[0].strip() + ": ")
                    pdf.set_font("Helvetica", style="", size=11)
                    pdf.write(8, parts[1].strip())
                    pdf.ln(10)
                else:
                    pdf.set_font("Helvetica", style="B", size=14)
                    pdf.multi_cell(0, 8, safe_header, new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(2)
                
                # If this header IS situation, set the flag
                if safe_header.lower() == "situation":
                    in_situation = True
            else:
                # Handle normal text
                pdf.set_font("Helvetica", size=11)
                safe_line = line.replace('—', '-').replace('–', '-').replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
                pdf.multi_cell(0, 6, safe_line, new_x="LMARGIN", new_y="NEXT")
                
        # If document ended while still in situation block
        if in_situation and os.path.exists(chart_path):
            pdf.image(chart_path, x=25, w=160)
            pdf.ln(10)

        # Embed Monte Carlo and analytics charts at end of brief
        charts_to_embed = [c for c in (analytics_charts or []) if c and os.path.exists(c)]
        if charts_to_embed:
            pdf.add_page()
            pdf.set_font("Helvetica", style="B", size=14)
            pdf.multi_cell(
                0, 8,
                "Strategic Analytics Exhibits",
                new_x="LMARGIN", new_y="NEXT",
            )
            pdf.ln(4)
            chart_titles = {
                "monte_carlo": "Exhibit A: Monte Carlo Win Probabilities",
                "weights_": "Exhibit B: Calibrated Decision Criteria",
                "option_scores_": "Exhibit C: Base-Case Weighted Option Scores",
            }
            for chart_path in charts_to_embed:
                title = "Analytics Chart"
                basename = os.path.basename(chart_path).lower()
                for key, label in chart_titles.items():
                    if key in basename:
                        title = label
                        break
                pdf.set_font("Helvetica", style="B", size=11)
                pdf.multi_cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                pdf.image(chart_path, x=15, w=180)
                pdf.ln(8)
        
        # Save PDF
        pdf.output(filename)
        
        # Clean up intermediate chart PNGs (keep only the final PDF)
        # Delete metrics chart
        if chart_path and os.path.exists(chart_path):
            try:
                os.remove(chart_path)
            except Exception:
                pass
        
        # Delete embedded analytics charts
        if analytics_charts:
            for agg_chart_path in analytics_charts:
                if agg_chart_path and os.path.exists(agg_chart_path):
                    try:
                        os.remove(agg_chart_path)
                    except Exception:
                        pass  # Silently skip if deletion fails
        
        return f"Successfully saved brief to {filename}"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Data unavailable: Failed to save brief for {company_name}. ({e})"
