from simple_salesforce import Salesforce
import os
from dotenv import load_dotenv
load_dotenv()

sf = Salesforce(
    username=os.getenv("SALESFORCE_USERNAME"),
    password=os.getenv("SALESFORCE_PASSWORD"),
    security_token=os.getenv("SALESFORCE_SECURITY_TOKEN")
)

print(f"Connected: {sf.sf_instance}")
result = sf.query("SELECT Id, CaseNumber, Subject, Status FROM Case LIMIT 3")
print(f"Cases found: {result['totalSize']}")

result = sf.query("SELECT Id, CaseNumber, Subject, Status, Priority, Description FROM Case LIMIT 3")
for case in result['records']:
    print(f"\nCase: {case['CaseNumber']}")
    print(f"  Subject:  {case['Subject']}")
    print(f"  Status:   {case['Status']}")
    print(f"  Priority: {case['Priority']}")