# B2B Lead Prospecting Pipeline

An AI-powered B2B lead prospecting pipeline built with **LangGraph** that automates company enrichment, contact discovery, and lead qualification against a configurable Ideal Customer Profile (ICP).

The system fetches leads from your CRM, enriches each company with firmographic data and recent business signals, discovers decision makers, scores the lead on a 0–100 scale with an A/B/C grade, and syncs the results back to your CRM — all automatically.

## Features

### **Multi-CRM Integration**
- Connect to **HubSpot**, **Airtable**, **Google Sheets**, or add your own CRM by extending the base class.

### **Automated Company Enrichment**
- **Website Scraping**: Extract industry, employee count, tech stack, and location from the company website.
- **Recent Signals**: Fetch and analyze recent news for funding rounds, hiring surges, product launches, and partnerships.
- **No Paid APIs**: All enrichment is inferred from publicly available web data via search and scraping.

### **Contact Discovery**
- Automatically find decision makers (C-suite, VPs, Directors) using web and LinkedIn search.
- Extract name, title, and email when available.

### **Lead Qualification & Scoring**
- **LLM-based scoring**: Evaluates each lead against your ICP across 5 dimensions (industry fit, size fit, funding fit, signal strength, tech fit) on a 0–100 scale.
- **Rule-based fallback**: If the LLM call fails, a deterministic scorer produces the same output structure.
- **Grade assignment**: A (≥70), B (≥45), C (<45) with disqualification reasons and recommended outreach angles.

### **CRM Sync**
- All scoring results, grades, qualification status, pain points, and outreach angles are written back to your CRM automatically.

## System Workflow

```
get_new_leads → check_remaining_leads → enrich_company → discover_contacts → qualify_lead → sync_to_crm → (loop back)
```

1. **Fetch Leads**: Pull new leads from your CRM.
2. **Enrich Company**: Scrape the company website and recent news to populate firmographic data and business signals.
3. **Discover Contacts**: Search for decision makers at the company.
4. **Qualify Lead**: Score against your ICP using an LLM (with rule-based fallback). Produces score, grade, qualified status, pain points, and outreach angle.
5. **Sync to CRM**: Write all results back to the CRM record.
6. **Loop**: Process the next lead until none remain.

## Configuration

### ICP Config (`config.yaml`)

Define your Ideal Customer Profile at the project root:

```yaml
target_industries: ["SaaS", "Data SaaS"]
min_employees: 50
max_employees: 600
funding_stages: ["Series B", "Series C"]
target_locations: ["United States"]
target_tech: ["Stripe", "AWS", "GCP"]
```

The qualification prompt and rule-based scorer both use these values.

## Integration with APIs

- **Airtable CRM**: [Sign up](https://www.airtable.com/) and create a contacts table with relevant fields.
- **HubSpot CRM**: [Sign up](https://www.hubspot.com/), create a private app, and get your API key.
- **Google Searches**: Perform web searches using the **Serper API**. [Get your API key here](https://serper.dev).
- **LLM**: Uses **Google Gemini Flash** via `langchain_google_genai`. [Get your API key here](https://ai.google.dev/gemini-api/docs/api-key).
- **Google APIs** (optional): Used for **Google Sheets** CRM and **Gmail**. Follow [this guide](https://developers.google.com/gmail/api/quickstart/python).

## Tech Stack

- **[LangGraph](https://langchain-ai.github.io/langgraph/)**: State machine framework for the prospecting workflow.
- **[LangChain](https://python.langchain.com/docs/introduction/)**: LLM abstraction and tooling.
- **Google Gemini Flash**: Primary LLM for enrichment and qualification.
- **PyYAML**: ICP configuration loading.

## How to Run

### Prerequisites

- Python 3.9+
- Google Gemini API key
- Serper API key
- CRM credentials (check `.env.example`)

### Setup

1. **Clone the repository:**

   ```sh
   git clone https://github.com/kaymen99/sales-outreach-automation-langgraph.git
   cd sales-outreach-automation-langgraph
   ```

2. **Create and activate a virtual environment:**

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   ```bash
   cp .env.example .env
   ```

   Open `.env` and add your API keys.

5. **Configure your ICP:**

   Edit `config.yaml` with your target industries, employee range, funding stages, locations, and tech stack.

---

### Start the Pipeline

```sh
python main.py
```

The system connects to your CRM, fetches new leads, enriches each company, discovers contacts, qualifies leads, and syncs results back.

---

### Customizing

- **Change your ICP**: Edit `config.yaml` — no code changes needed.
- **Add a custom CRM**: Extend `LeadLoaderBase` in `src/tools/leads_loader/lead_loader_base.py`.
- **Adjust scoring**: Modify `LEAD_QUALIFICATION_PROMPT` in `src/prompts.py` or the rule-based fallback in `src/scorer.py`.
- **Add enrichment sources**: Extend `src/tools/enrichment.py`.

## Project Structure

```
├── config.yaml                 # ICP configuration
├── main.py                     # Entry point
├── requirements.txt
├── src/
│   ├── graph.py                # LangGraph workflow wiring
│   ├── nodes.py                # All pipeline node logic
│   ├── prompts.py              # LLM prompts
│   ├── scorer.py               # Rule-based scoring fallback
│   ├── state.py                # Graph state schema
│   ├── utils.py                # LLM invocation, Google auth
│   └── tools/
│       ├── enrichment.py       # Company data enrichment
│       ├── contact_discovery.py # Decision maker discovery
│       ├── base/
│       │   ├── search_tools.py       # Google search & news
│       │   ├── markdown_scraper_tool.py
│       │   ├── gmail_tools.py
│       │   └── linkedin_tools.py
│       └── leads_loader/
│           ├── lead_loader_base.py
│           ├── airtable.py
│           ├── google_sheets.py
│           └── hubspot.py
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Contact

For questions or suggestions, contact `aymenMir1001@gmail.com`.
