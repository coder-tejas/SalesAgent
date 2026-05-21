import json
from src.utils import invoke_llm
from src.tools.base.search_tools import google_search, get_recent_news
from src.tools.base.markdown_scraper_tool import scrape_website_to_markdown


ENRICHMENT_PROMPT = """
You are a B2B company intelligence analyst. Analyze the provided website content and news about a company and extract the following information in JSON format only:

1. industry: The primary industry or vertical the company operates in.
2. employee_count: Estimated number of employees (use a number, or 0 if unknown).
3. funding_stage: The company's funding stage (e.g., Bootstrapped, Seed, Series A, Series B, Series C, Series D+, Public). Use "Unknown" if not determinable.
4. tech_stack: A list of technologies the company uses, inferred from the website content (e.g., AWS, GCP, Stripe, React, etc.). Return an empty list if none found.
5. location: The company's headquarters location (city, country or city, state).

Return JSON only with this exact structure:
{{
  "industry": "",
  "employee_count": 0,
  "funding_stage": "",
  "tech_stack": [],
  "location": ""
}}
"""


def enrich_company(domain: str, company_name: str) -> dict:
    """
    Enrich company data by scraping their website and fetching recent news.
    Returns a dict with industry, employee_count, funding_stage, tech_stack, location, and recent_signals.
    """
    website_url = f"https://{domain}" if not domain.startswith("http") else domain

    website_summary = ""
    recent_news = ""
    recent_signals = []

    try:
        website_summary = scrape_website_to_markdown(website_url)
    except Exception:
        website_summary = "Website could not be scraped."

    try:
        recent_news = get_recent_news(company=company_name)
    except Exception:
        recent_news = "Recent news could not be fetched."

    inputs = f"""
Website content for {company_name} ({website_url}):
{website_summary[:8000]}

Recent news about {company_name}:
{recent_news[:4000]}
"""

    try:
        result = invoke_llm(
            system_prompt=ENRICHMENT_PROMPT,
            user_message=inputs,
            model="gemini-1.5-flash",
        )
        company_data = json.loads(result)
    except Exception:
        company_data = {
            "industry": "",
            "employee_count": 0,
            "funding_stage": "",
            "tech_stack": [],
            "location": "",
        }

    try:
        signals_prompt = """
You are a business intelligence analyst. Extract recent business signals/events from the provided news content.
Signals include: funding rounds, hiring surges, product launches, partnerships, executive changes, expansions.

Return a JSON list of strings, each describing one signal. If no signals found, return an empty list.
Return JSON only.
"""
        signals_result = invoke_llm(
            system_prompt=signals_prompt,
            user_message=recent_news[:4000],
            model="gemini-1.5-flash",
        )
        recent_signals = json.loads(signals_result)
        if not isinstance(recent_signals, list):
            recent_signals = []
    except Exception:
        recent_signals = []

    return {
        "industry": company_data.get("industry", ""),
        "employee_count": company_data.get("employee_count", 0),
        "funding_stage": company_data.get("funding_stage", ""),
        "tech_stack": company_data.get("tech_stack", []),
        "location": company_data.get("location", ""),
        "recent_signals": recent_signals,
        "website_summary": website_summary[:3000],
        "recent_news": recent_news[:3000],
    }
