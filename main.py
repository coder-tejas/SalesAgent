import os
from dotenv import load_dotenv
from src.graph import OutReachAutomation
from src.tools.leads_loader.airtable import AirtableLeadLoader

load_dotenv()

if __name__ == "__main__":
    lead_loader = AirtableLeadLoader(
        access_token=os.getenv("AIRTABLE_ACCESS_TOKEN"),
        base_id=os.getenv("AIRTABLE_BASE_ID"),
        table_name=os.getenv("AIRTABLE_TABLE_NAME"),
    )

    automation = OutReachAutomation(lead_loader)
    app = automation.app

    inputs = {"leads_ids": []}

    config = {'recursion_limit': 1000}
    output = app.invoke(inputs, config)
    print(output)
