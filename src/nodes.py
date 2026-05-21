import json
import yaml
import os
from colorama import Fore, Style
from .tools.base.search_tools import google_search
from .tools.enrichment import enrich_company
from .tools.contact_discovery import discover_contacts
from .prompts import LEAD_QUALIFICATION_PROMPT
from .state import GraphInputState, GraphState
from .utils import invoke_llm
from .scorer import score_lead as rule_based_score


def load_icp_config() -> dict:
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


class OutReachAutomationNodes:
    def __init__(self, loader):
        self.lead_loader = loader
        self.icp = load_icp_config()

    def get_new_leads(self, state: GraphInputState):
        print(Fore.YELLOW + "----- Fetching new leads -----\n" + Style.RESET_ALL)

        raw_leads = self.lead_loader.fetch_records()

        leads = []
        for lead in raw_leads:
            leads.append({
                "id": lead.get("id", ""),
                "name": f'{lead.get("First Name", "")} {lead.get("Last Name", "")}'.strip(),
                "email": lead.get("Email", ""),
                "phone": lead.get("Phone", ""),
                "address": lead.get("Address", ""),
                "company_name": lead.get("Company Name", lead.get("Company", "")),
                "company_domain": lead.get("Company Domain", lead.get("Website", "")),
            })

        print(Fore.YELLOW + f"----- Fetched {len(leads)} leads -----\n" + Style.RESET_ALL)
        return {"leads": leads, "number_leads": len(leads)}

    @staticmethod
    def check_remaining_leads(state: GraphState):
        print(Fore.YELLOW + "----- Checking for remaining leads -----\n" + Style.RESET_ALL)

        current_lead = None
        if state.get("leads"):
            current_lead = state["leads"].pop()
        return {"current_lead": current_lead}

    @staticmethod
    def check_if_more_leads(state: GraphState):
        num_leads = state.get("number_leads", 0)
        if num_leads > 0:
            print(Fore.YELLOW + f"----- Found {num_leads} more leads -----\n" + Style.RESET_ALL)
            return "Found leads"
        else:
            print(Fore.GREEN + "----- Finished, No more leads -----\n" + Style.RESET_ALL)
            return "No more leads"

    def enrich_company(self, state: GraphState):
        print(Fore.YELLOW + "----- Enriching company data -----\n" + Style.RESET_ALL)

        current_lead = state.get("current_lead", {})
        company_name = current_lead.get("company_name", "")
        company_domain = current_lead.get("company_domain", "")

        company_data = {
            "industry": "",
            "employee_count": 0,
            "funding_stage": "",
            "tech_stack": [],
            "location": "",
        }
        recent_signals = []
        website_summary = ""
        recent_news = ""

        if company_domain or company_name:
            domain = company_domain or company_name.lower().replace(" ", "") + ".com"
            try:
                enrichment = enrich_company(domain, company_name)
                company_data = {
                    "industry": enrichment.get("industry", ""),
                    "employee_count": enrichment.get("employee_count", 0),
                    "funding_stage": enrichment.get("funding_stage", ""),
                    "tech_stack": enrichment.get("tech_stack", []),
                    "location": enrichment.get("location", ""),
                }
                recent_signals = enrichment.get("recent_signals", [])
                website_summary = enrichment.get("website_summary", "")
                recent_news = enrichment.get("recent_news", "")
            except Exception as e:
                print(Fore.RED + f"Company enrichment failed: {e}\n" + Style.RESET_ALL)

        return {
            "company_data": company_data,
            "recent_signals": recent_signals,
            "current_lead": {**current_lead, "website_summary": website_summary, "recent_news": recent_news},
        }

    def discover_contacts(self, state: GraphState):
        print(Fore.YELLOW + "----- Discovering decision makers -----\n" + Style.RESET_ALL)

        current_lead = state.get("current_lead", {})
        company_name = current_lead.get("company_name", "")
        company_domain = current_lead.get("company_domain", "")

        contacts = []
        if company_name:
            domain = company_domain or company_name.lower().replace(" ", "") + ".com"
            try:
                contacts = discover_contacts(company_name, domain)
            except Exception as e:
                print(Fore.RED + f"Contact discovery failed: {e}\n" + Style.RESET_ALL)

        return {"contacts": contacts}

    def qualify_lead(self, state: GraphState):
        print(Fore.YELLOW + "----- Qualifying lead -----\n" + Style.RESET_ALL)

        current_lead = state.get("current_lead", {})
        company_data = state.get("company_data", {})
        recent_signals = state.get("recent_signals", [])

        company_name = current_lead.get("company_name", "")
        industry = company_data.get("industry", "")
        employees = company_data.get("employee_count", 0)
        funding_stage = company_data.get("funding_stage", "")
        location = company_data.get("location", "")
        tech_stack = company_data.get("tech_stack", [])
        website_summary = current_lead.get("website_summary", "")
        recent_news = current_lead.get("recent_news", "")

        icp = self.icp
        target_industries = ", ".join(icp.get("target_industries", []))
        min_employees = icp.get("min_employees", 50)
        max_employees = icp.get("max_employees", 600)
        funding_stages = ", ".join(icp.get("funding_stages", []))
        target_locations = ", ".join(icp.get("target_locations", []))
        target_tech = ", ".join(icp.get("target_tech", []))

        prompt = LEAD_QUALIFICATION_PROMPT.format(
            target_industries=target_industries,
            min_employees=min_employees,
            max_employees=max_employees,
            funding_stages=funding_stages,
            target_locations=target_locations,
            target_tech=target_tech,
            company_name=company_name,
            industry=industry,
            employees=employees,
            funding_stage=funding_stage,
            location=location,
            tech_stack=", ".join(tech_stack),
            recent_signals=", ".join(recent_signals) if recent_signals else "No recent signals",
            website_summary=website_summary[:2000] if website_summary else "No website data available",
            recent_news=recent_news[:2000] if recent_news else "No recent news available",
        )

        qualification_result = {}
        try:
            result = invoke_llm(
                system_prompt="",
                user_message=prompt,
                model="gemini-1.5-flash",
            )
            qualification_result = json.loads(result)
        except Exception as e:
            print(Fore.RED + f"LLM qualification failed, falling back to rule-based scorer: {e}\n" + Style.RESET_ALL)
            qualification_result = rule_based_score(
                industry=industry,
                employee_count=employees,
                funding_stage=funding_stage,
                location=location,
                tech_stack=tech_stack,
                recent_signals=recent_signals,
                target_industries=icp.get("target_industries", []),
                min_employees=min_employees,
                max_employees=max_employees,
                funding_stages=icp.get("funding_stages", []),
                target_locations=icp.get("target_locations", []),
                target_tech=icp.get("target_tech", []),
            )

        score = qualification_result.get("total_score", 0)
        grade = qualification_result.get("grade", "C")
        qualified = qualification_result.get("qualified", False)
        disqualification_reason = qualification_result.get("disqualification_reason", "")
        pain_points = qualification_result.get("pain_points", [])
        outreach_angle = qualification_result.get("outreach_angle", "")

        print(Fore.CYAN + f"Score: {score}, Grade: {grade}, Qualified: {qualified}\n" + Style.RESET_ALL)

        return {
            "score": score,
            "grade": grade,
            "qualified": qualified,
            "disqualification_reason": disqualification_reason,
            "pain_points": pain_points,
            "outreach_angle": outreach_angle,
        }

    def sync_to_crm(self, state: GraphState):
        print(Fore.YELLOW + "----- Syncing to CRM -----\n" + Style.RESET_ALL)

        current_lead = state.get("current_lead", {})
        lead_id = current_lead.get("id", "")

        new_data = {
            "Score": state.get("score", 0),
            "Grade": state.get("grade", "C"),
            "Qualified": state.get("qualified", False),
            "Outreach Angle": state.get("outreach_angle", ""),
            "Pain Points": ", ".join(state.get("pain_points", [])),
            "Disqualification Reason": state.get("disqualification_reason", ""),
        }

        if lead_id:
            try:
                self.lead_loader.update_record(lead_id, new_data)
            except Exception as e:
                print(Fore.RED + f"CRM sync failed: {e}\n" + Style.RESET_ALL)

        return {"crm_synced": True, "number_leads": state.get("number_leads", 0) - 1}
