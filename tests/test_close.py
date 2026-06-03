# test_close.py
from salesforce_agent import run_agent

case_id = "500fj00001OKx6aAAD"
result = run_agent(f"Close case {case_id} — issue resolved after escalation, customer satisfied")
print(f"AGENT: {result}")