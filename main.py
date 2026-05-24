import os
import sys
import re
import argparse
import datetime
import litellm
from crewai import Crew, Process

# Fix for Windows console unicode errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# --- HOTFIX FOR CREWAI + GROQ BUG ---
original_completion = litellm.completion
def patched_completion(*args, **kwargs):
    if 'messages' in kwargs:
        for msg in kwargs['messages']:
            if 'cache_breakpoint' in msg:
                del msg['cache_breakpoint']
    return original_completion(*args, **kwargs)
litellm.completion = patched_completion
# ------------------------------------


from tools import (
    save_brief,
    parse_waterfall,
    parse_pullquote,
    parse_risk_register,
    generate_waterfall_chart,
    generate_options_radar_chart,
    generate_risk_matrix_chart
)

_OPTION_LINE_RE = re.compile(
    r"^(.+?)\s*\|\s*P&L:\s*(\d+(?:\.\d+)?)\s*\|\s*Feasibility:\s*(\d+(?:\.\d+)?)\s*\|\s*"
    r"CustomerRisk:\s*(\d+(?:\.\d+)?)\s*\|\s*Speed:\s*(\d+(?:\.\d+)?)\s*\|\s*"
    r"OpComplexity:\s*(\d+(?:\.\d+)?)\s*\|\s*CompDefense:\s*(\d+(?:\.\d+)?)\s*\|\s*"
    r"RegRisk:\s*(\d+(?:\.\d+)?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

def parse_option_scores(text: str) -> dict:
    if not re.search(r"OPTION_SCORES:", text, re.IGNORECASE):
        return {}
    block_match = re.search(
        r"OPTION_SCORES:\s*(.*?)(?=\n\s*(?:FINANCIAL ANGLE:|##\s*METRICS|#\s*StratAgent|PULLQUOTE|$))",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not block_match:
        return {}
    block_text = block_match.group(1)
    options = {}
    for line_match in _OPTION_LINE_RE.finditer(block_text):
        option_name = line_match.group(1).strip()
        options[option_name] = {
            "P&L": float(line_match.group(2)),
            "Feasibility": float(line_match.group(3)),
            "CustomerRisk": float(line_match.group(4)),
            "Speed": float(line_match.group(5)),
            "OpComplexity": float(line_match.group(6)),
            "CompDefense": float(line_match.group(7)),
            "RegRisk": float(line_match.group(8)),
        }
    return options

def main():
    parser = argparse.ArgumentParser(description="StratAgent")
    parser.add_argument("--company", type=str, required=True, help="Company name to research")
    parser.add_argument("--problem", type=str, required=True, help="Business problem to analyze")
    args = parser.parse_args()
    company = args.company
    problem = args.problem

    print("\n" + "="*50)
    print("Starting StratAgent...")
    print(f"Company: {company}")
    print(f"Problem: {problem}")
    print("="*50 + "\n")

    try:
        from tools import fetch_news, fetch_financials, save_brief, parse_pullquote
        import time

        print("Fetching News and Financials natively...")
        news_data = fetch_news(company)
        financials_data = fetch_financials(company)
        
        research_data = f"News: {news_data}\n\nFinancials: {financials_data}"

        from agents import get_strategist, get_partner
        from tasks import get_drafting_task, get_critique_task, get_final_polish_task

        strategist = get_strategist()
        partner = get_partner()

        draft_task = get_drafting_task()
        critique_task = get_critique_task()
        final_task = get_final_polish_task()

        print("\n" + "="*50)
        print("PHASE 1: Principal Strategist Drafting Strategy")
        print("="*50 + "\n")
        
        crew_1 = Crew(agents=[strategist], tasks=[draft_task], verbose=True)
        draft_result = str(crew_1.kickoff(inputs={
            "company_name": company, 
            "problem": problem,
            "research_data": research_data
        }))

        print("\n[PAUSING FOR 65 SECONDS to reset Free Tier Quota...]\n")
        time.sleep(65)

        print("\n" + "="*50)
        print("PHASE 2: Senior Partner Critiquing Draft")
        print("="*50 + "\n")

        crew_2 = Crew(agents=[partner], tasks=[critique_task], verbose=True)
        critique_result = str(crew_2.kickoff(inputs={
            "company_name": company,
            "problem": problem,
            "draft_strategy": draft_result
        }))

        print("\n[PAUSING FOR 65 SECONDS to reset Free Tier Quota...]\n")
        time.sleep(65)

        print("\n" + "="*50)
        print("PHASE 3: Principal Strategist Final Polish")
        print("="*50 + "\n")

        crew_3 = Crew(agents=[strategist], tasks=[final_task], verbose=True)
        final_result = str(crew_3.kickoff(inputs={
            "company_name": company,
            "problem": problem,
            "draft_strategy": draft_result,
            "partner_critique": critique_result
        }))

        pullquote = parse_pullquote(final_result)
        
        save_msg = save_brief(final_result, company, problem, 
                            analytics_charts=[],
                            pullquote=pullquote,
                            risk_data=[])

        print("\n" + "="*50)
        print("FINAL CONSULTING BRIEF")
        print("="*50 + "\n")
        print(final_result)
        print("\n" + "="*50)
        print(save_msg)
        print("="*50 + "\n")

    except Exception as e:
        print(f"\nAn error occurred while running the AI Crew: {e}")

if __name__ == "__main__":
    main()
