from langgraph.graph import END, StateGraph
from .nodes import OutReachAutomationNodes
from .state import GraphState
from .tools.leads_loader.lead_loader_base import LeadLoaderBase


class OutReachAutomation:
    def __init__(self, loader: LeadLoaderBase):
        self.app = self.build_graph(loader)

    def build_graph(self, loader):
        graph = StateGraph(GraphState)
        nodes = OutReachAutomationNodes(loader)

        graph.add_node("get_new_leads", nodes.get_new_leads)
        graph.add_node("check_remaining_leads", nodes.check_remaining_leads)
        graph.add_node("enrich_company", nodes.enrich_company)
        graph.add_node("discover_contacts", nodes.discover_contacts)
        graph.add_node("qualify_lead", nodes.qualify_lead)
        graph.add_node("sync_to_crm", nodes.sync_to_crm)

        graph.set_entry_point("get_new_leads")

        graph.add_edge("get_new_leads", "check_remaining_leads")

        graph.add_conditional_edges(
            "check_remaining_leads",
            nodes.check_if_more_leads,
            {
                "Found leads": "enrich_company",
                "No more leads": END,
            },
        )

        graph.add_edge("enrich_company", "discover_contacts")
        graph.add_edge("discover_contacts", "qualify_lead")

        graph.add_conditional_edges(
            "qualify_lead",
            lambda state: "qualified" if state.get("qualified", False) else "not_qualified",
            {
                "qualified": "sync_to_crm",
                "not_qualified": "sync_to_crm",
            },
        )

        graph.add_edge("sync_to_crm", "check_remaining_leads")

        return graph.compile()
