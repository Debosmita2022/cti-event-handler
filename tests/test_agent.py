# Get the ID of case 00001002 first
import json
from salesforce_agent import run_agent
from salesforce_cases import get_sf_connection
from simple_salesforce import Salesforce

sf = get_sf_connection()
result = sf.query("SELECT Id FROM Case WHERE CaseNumber = '00001002' LIMIT 1")
case_id = result['records'][0]['Id']

print(f"\n{'='*50}")
print(f"INSTRUCTION: Escalate case {case_id} — customer is a VIP reporting repeated failures")
print(f"{'='*50}")
result = run_agent(f"Escalate case {case_id} — customer is a VIP reporting repeated failures")
print(f"AGENT: {result}")

print(f"\n{'='*50}")
print(f"INSTRUCTION: Close case {case_id} — issue resolved after escalation, customer satisfied")
print(f"{'='*50}")
result = run_agent(f"Close case {case_id} — issue resolved after escalation, customer satisfied")
print(f"AGENT: {result}")