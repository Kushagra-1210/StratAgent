# StratAgent
**Autonomous AI Strategy Consulting Agent**

> *Research any company. Debate the options. Get a consulting brief. In 5 minutes. For free.*

---

## What is StratAgent?

StratAgent is an autonomous two-agent AI system modeled after an MBB consulting engagement team. It researches a company using live financial data and news, conducts an adversarial strategic debate between two AI personas, and delivers a professionally formatted PDF consulting brief.

Built by a 2nd year CS student. Zero infrastructure cost.

---

## Live Demo

**Sample Output 1:** [`samples/sample_brief_Paytm.pdf`](samples/sample_brief_Paytm.pdf)
*Paytm — Path to profitability amid competition from PhonePe and GPay*

**Sample Output 2:** [`samples/sample_brief_Zomato.pdf`](samples/sample_brief_Zomato.pdf)
*Zomato — Gig Worker Strike Impact on Operations and Long Term Strategy*

---

## Architecture

```
INPUT
python main.py --company "Zomato" --problem "Gig worker strike impact"
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 1 — DATA GATHERING                           │
│  • Scrapes live financial metrics from Screener.in  │
│  • Fetches latest news from Google News RSS         │
│  • Selects optimal analytical framework             │
└─────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 2 — PRINCIPAL STRATEGIST                     │
│  • Analyzes data through selected MBB framework     │
│  • Identifies Strategic Tension                     │
│  • Proposes 3 company-specific strategic options    │
│  • Writes structured first draft                    │
└─────────────────────────────────────────────────────┘
      │  [65s pause — Groq rate limit management]
      ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 3 — SENIOR PARTNER (DEVIL'S ADVOCATE)        │
│  • Critiques the draft rigorously                   │
│  • Identifies logical gaps and blind spots          │
│  • Issues 3 directives for improvement              │
└─────────────────────────────────────────────────────┘
      │  [65s pause]
      ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 4 — FINAL POLISH                             │
│  • Incorporates all critique                        │
│  • Expands risk analysis and roadmaps               │
│  • Writes final consulting brief                    │
└─────────────────────────────────────────────────────┘
      │
      ▼
OUTPUT — Professional PDF saved to output/
  • Framework citation (author + year)
  • Situation with live financial data
  • Strategic Tension
  • 3 Strategic Options
  • Recommendation
  • Data Confidence Score (1-5 based on source gaps)
  • Financial Metrics 1x2 Subplot (Returns vs. Valuation)
  • Generation Runtime Analytics
```

---

## Why Adversarial Architecture?

Single-pass AI outputs are overconfident — they never challenge their own assumptions.

Real MBB consulting teams use senior partners to stress-test analyst recommendations before they reach clients. StratAgent replicates this process: a Strategist proposes, a Devil's Advocate identifies weaknesses, the Strategist refines.

The result is more rigorous, more balanced, and more honest than any single-pass generation.

---

## Framework Selection Logic

StratAgent dynamically selects the most appropriate analytical framework using 10 priority-ordered rules based on the problem type:

| Framework | Author | Year | Used For |
|---|---|---|---|
| Treacy & Wiersema Value Disciplines | Treacy & Wiersema | 1995 | Strategic positioning, value proposition |
| Porter's Five Forces | Michael Porter | 1979 | Competitive dynamics, market entry |
| Ansoff Matrix | Igor Ansoff | 1957 | Growth strategies, expansion |
| Value Chain Analysis | Michael Porter | 1985 | Cost reduction, profitability |
| McKinsey 7S | Peters & Waterman | 1980 | Organizational alignment, internal gaps |
| BCG Matrix | Bruce Henderson | 1970 | Portfolio decisions, resource allocation |
| Scenario Planning | Shell/GBN | 1970s | Macro uncertainty, regulatory risk |
| Jobs To Be Done | Clayton Christensen | 2016 | Customer behavior, product innovation |
| VRIO Framework | Jay Barney | 1991 | Competitive advantage sustainability |
| MECE Issue Tree | McKinsey standard | — | Root cause analysis, problem decomposition |

---

## Tech Stack

| Tool | Purpose | Cost |
|---|---|---|
| CrewAI | Multi-agent orchestration | Free |
| Groq API — Llama 3.3 70B | LLM inference | Free |
| Screener.in | Live financial metrics | Free |
| Google News RSS | Live news headlines | Free |
| FPDF2 | PDF generation | Free |
| Matplotlib | Financial charts | Free |
| Python 3.11 | Core language | Free |

**Total infrastructure cost: ₹0/month**

---

## Quick Start

**Prerequisites:** Python 3.9+, free Groq API key from [console.groq.com](https://console.groq.com)

```bash
# 1. Clone
git clone https://github.com/Kushagra-1210/StratAgent.git
cd StratAgent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure — create a .env file in the project root
echo "GROQ_API_KEY=your_key_here" > .env

# 4. Run
python main.py --company "Zomato" --problem "Impact of fuel price hike on profitability"
```

Output PDF appears in the `output/` folder.

---

## Example Queries

```bash
# Food delivery — operational problem
python main.py --company "Zomato" --problem "Gig worker strike impact on operations"

# Jewellery — market problem
python main.py --company "Titan" --problem "Impact of gold advisory on revenue"

# IT services — macro problem
python main.py --company "Infosys" --problem "US visa restrictions impact on revenue growth"

# Fintech — competitive problem
python main.py --company "Paytm" --problem "Path to profitability amid competition"
```

---

## Project Structure

```
StratAgent/
├── main.py           # Entry point — CLI args, crew orchestration, PDF save
├── agents.py         # Two AI agents — Principal Strategist + Senior Partner
├── tasks.py          # Three tasks — Draft, Critique, Final Polish
├── tools.py          # Data layer — Screener.in scraper, News RSS, PDF engine
├── requirements.txt  # Dependencies
├── samples/          # Sample PDF outputs
└── .gitignore        # Excludes .env, output/, .venv/
```

---

## Data Sources & Limitations

**Live data fetched on every run:**
- Financial metrics via Screener.in (Market Cap, ROCE, ROE, PE Ratio, Price)
- News via Google News RSS (latest headlines)

**Known limitations:**
- News content is headline-only — full articles are behind paywalls
- Financial data limited to metrics available on Screener.in public pages
- Analysis quality improves with companies that have strong news coverage

---

## About

Built by **Kushagra Bansal**
B.Tech Computer Science & Engineering — Shiv Nadar University (2024–28)

[LinkedIn](https://www.linkedin.com/in/kushagra-kb1210) · [GitHub](https://github.com/Kushagra-1210)

---

*StratAgent is a portfolio project demonstrating autonomous AI agent architecture applied to strategic analysis. It is not a substitute for professional consulting advice.*
