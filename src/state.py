from typing import List
from typing_extensions import TypedDict


class CompanyData(TypedDict, total=False):
    industry: str
    employee_count: int
    funding_stage: str
    tech_stack: List[str]
    location: str


class Contact(TypedDict, total=False):
    name: str
    title: str
    email: str


class GraphInputState(TypedDict):
    leads_ids: List[str]


class GraphState(TypedDict, total=False):
    leads: List[dict]
    current_lead: dict
    company_data: CompanyData
    recent_signals: List[str]
    contacts: List[Contact]
    score: int
    grade: str
    qualified: bool
    disqualification_reason: str
    pain_points: List[str]
    outreach_angle: str
    crm_synced: bool
    number_leads: int
