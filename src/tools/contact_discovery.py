import json
import re
from src.utils import invoke_llm
from src.tools.base.search_tools import google_search


CONTACT_DISCOVERY_PROMPT = """
You are a B2B contact researcher. Based on the provided web search results about a company's leadership team, extract decision makers.

For each person found, extract:
- name: Full name
- title: Job title (CEO, CTO, VP of Marketing, etc.)
- email: Email address if visible, otherwise ""

Focus on C-suite, VPs, Directors, and Heads of departments.

Return JSON only with this exact structure:
[
  {"name": "", "title": "", "email": ""},
  {"name": "", "title": "", "email": ""}
]

If no contacts found, return an empty list.
"""


def discover_contacts(company_name: str, domain: str) -> list[dict]:
    """
    Find decision makers at a company using web searches.
    Returns a list of dicts with name, title, and email.
    """
    search_queries = [
        f"CEO of {company_name} site:linkedin.com",
        f"{company_name} leadership team executives",
        f"{company_name} CTO VP marketing site:linkedin.com",
        f"{company_name} decision makers email {domain}",
    ]

    all_results = []
    for query in search_queries:
        try:
            results = google_search(query)
            all_results.extend(results)
        except Exception:
            continue

    if not all_results:
        return []

    search_text = json.dumps(all_results, indent=2)

    try:
        result = invoke_llm(
            system_prompt=CONTACT_DISCOVERY_PROMPT,
            user_message=search_text[:8000],
            model="gemini-1.5-flash",
        )
        contacts = json.loads(result)
        if not isinstance(contacts, list):
            return []
        return contacts
    except Exception:
        return []


def extract_email_from_search(company_name: str, domain: str) -> str:
    """
    Attempt to find a generic company email pattern from search results.
    """
    try:
        query = f"{company_name} contact email site:{domain}"
        results = google_search(query)
        text = json.dumps(results)

        email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
        emails = email_pattern.findall(text)

        for email in emails:
            if domain in email:
                return email
    except Exception:
        pass
    return ""
