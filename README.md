# StratAgent

### Autonomous AI Strategy Consulting Agent

Single-pass AI outputs are often overconfident and unchallenged.

Real strategy requires stress-testing — a devil’s advocate who finds the gaps before the client does.

StratAgent replicates the MBB consulting workflow: a Principal Strategist drafts, a Senior Partner critiques, and the Strategist refines. The result is a structured consulting brief with live financial data, generated in minutes.

---

## Who This Is For

- **Founders and operators** who need structured strategic analysis without hiring a consulting firm
- **Analysts and Product Managers** who want a rigorous first-pass framework before building presentations
- **Case interview candidates** who want real-company strategic briefs for practice

---

## Sample Use Cases

### Paytm — Path to Profitability

Identified commission restructuring and platform fee optimization as primary value drivers. Recommended a phased implementation focused on UPI monetization before expanding credit products.

### Zomato — Gig Worker Strike Impact

Assessed operational disruption under multiple scenarios and recommended a hybrid employment model for high-density zones while maintaining flexibility elsewhere.

---

## Architecture

```text
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
│  • Analyzes data through selected framework         │
│  • Identifies strategic tension                     │
│  • Generates company-specific options               │
│  • Creates structured first draft                   │
└─────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 3 — SENIOR PARTNER                           │
│  • Critiques the draft rigorously                   │
│  • Identifies logical gaps and blind spots          │
│  • Issues improvement directives                    │
└─────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 4 — FINAL POLISH                             │
│  • Incorporates all critique                        │
│  • Expands risk analysis                            │
│  • Produces final consulting brief                  │
└─────────────────────────────────────────────────────┘
      │
      ▼
OUTPUT
Professional PDF Consulting Brief
```

---

## Why Adversarial Architecture?

Most AI-generated strategy recommendations are never challenged.

Consulting firms improve recommendation quality through internal review and debate before presenting to clients.

StratAgent follows the same principle:

1. **Strategist proposes**
2. **Senior Partner critiques**
3. **Strategist refines**

This creates recommendations that are more balanced, defensible, and realistic than a single-pass AI response.

---

## Framework Selection Logic

StratAgent dynamically selects the most appropriate framework based on the business problem.

| Framework            | Author              | Use Case                       |
| -------------------- | ------------------- | ------------------------------ |
| Porter's Five Forces | Michael Porter      | Competitive dynamics           |
| Ansoff Matrix        | Igor Ansoff         | Growth strategies              |
| Value Chain Analysis | Michael Porter      | Cost reduction & profitability |
| McKinsey 7S          | Peters & Waterman   | Organizational alignment       |
| BCG Matrix           | Bruce Henderson     | Portfolio decisions            |
| Scenario Planning    | Shell / GBN         | Regulatory & macro uncertainty |
| Jobs To Be Done      | Clayton Christensen | Customer behavior              |
| VRIO Framework       | Jay Barney          | Sustainable advantage          |
| Value Disciplines    | Treacy & Wiersema   | Strategic positioning          |
| MECE Issue Tree      | McKinsey            | Root-cause analysis            |

---

## Tech Stack

| Technology               | Purpose                   |
| ------------------------ | ------------------------- |
| CrewAI                   | Multi-agent orchestration |
| Groq API (Llama 3.3 70B) | LLM inference             |
| Screener.in              | Financial data            |
| Google News RSS          | News intelligence         |
| FPDF2                    | PDF generation            |
| Matplotlib               | Visualizations            |
| Python 3.11              | Core development          |

---

## Features

* Multi-agent consulting workflow
* Automatic framework selection
* Live financial data integration
* Live news intelligence
* Strategic tension identification
* Scenario-based recommendations
* Structured PDF consulting brief generation
* Risk and implementation roadmap analysis

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Kushagra-1210/StratAgent.git
cd StratAgent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
```

### 4. Run the Agent

```bash
python main.py --company "Zomato" --problem "Impact of fuel price hike on profitability"
```

Generated reports will be saved in the `output/` directory.

---

## Example Queries

```bash
python main.py --company "Zomato" \
--problem "Gig worker strike impact on operations"

python main.py --company "Titan" \
--problem "Impact of gold price volatility on revenue"

python main.py --company "Infosys" \
--problem "US visa restrictions impact on growth"

python main.py --company "Paytm" \
--problem "Path to profitability amid competition"
```

---

## Project Structure

```text
StratAgent/
├── main.py
├── agents.py
├── tasks.py
├── tools.py
├── requirements.txt
├── samples/
├── output/
└── .gitignore
```

---

## Data Sources

### Financial Data

* Market Capitalization
* ROE
* ROCE
* PE Ratio
* Current Share Price

Source: Screener.in

### News Data

* Latest company-related headlines
* Industry developments
* Macro-economic events

Source: Google News RSS

---

## Limitations

* News analysis relies on publicly available headlines
* Some companies may have limited media coverage
* Financial data availability depends on public disclosures
* Outputs are intended for strategic exploration, not investment or consulting advice

---

## Author

**Kushagra Bansal**

B.Tech Computer Science & Engineering  
Shiv Nadar University (2024–2028)

[GitHub](https://github.com/Kushagra-1210) • [LinkedIn](https://www.linkedin.com/in/kushagra-kb1210)

---

## Disclaimer

StratAgent is a portfolio project demonstrating autonomous AI-agent architecture applied to strategic consulting workflows.

It is not a substitute for professional consulting, legal, financial, or investment advice.

