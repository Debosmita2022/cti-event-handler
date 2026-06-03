from simple_salesforce import Salesforce
from logger import get_logger
import os
from dotenv import load_dotenv

load_dotenv()
log = get_logger("salesforce_cases")

def get_sf_connection() -> Salesforce:
    return Salesforce(
        username=os.getenv("SALESFORCE_USERNAME"),
        password=os.getenv("SALESFORCE_PASSWORD"),
        security_token=os.getenv("SALESFORCE_SECURITY_TOKEN")
    )

# ── READ ─────────────────────────────────────────────────────────

def get_case_by_id(sf: Salesforce, case_id: str) -> dict:
    log.info(f"get_case_by_id | case_id={case_id}")
    result = sf.query(f"""
        SELECT Id, CaseNumber, Subject, Status, Priority,
               Description, AccountId, ContactId, OwnerId
        FROM Case
        WHERE Id = '{case_id}'
        LIMIT 1
    """)
    if result['totalSize'] == 0:
        log.warning(f"get_case_by_id | case_id={case_id} | NOT FOUND")
        return None
    case = result['records'][0]
    log.info(f"get_case_by_id | found | CaseNumber={case['CaseNumber']} | Status={case['Status']}")
    return case

def get_cases_by_phone(sf: Salesforce, phone: str) -> list:
    log.info(f"get_cases_by_phone | phone={phone}")
    result = sf.query(f"""
        SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate
        FROM Case
        WHERE Contact.Phone = '{phone}'
        OR Account.Phone = '{phone}'
        ORDER BY CreatedDate DESC
        LIMIT 5
    """)
    log.info(f"get_cases_by_phone | phone={phone} | found={result['totalSize']}")
    return result['records']

def get_open_cases(sf: Salesforce) -> list:
    log.info("get_open_cases | querying")
    result = sf.query("""
        SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate
        FROM Case
        WHERE Status != 'Closed'
        ORDER BY Priority DESC, CreatedDate ASC
        LIMIT 10
    """)
    log.info(f"get_open_cases | found={result['totalSize']}")
    return result['records']

# ── CREATE ───────────────────────────────────────────────────────

def create_case(sf: Salesforce, subject: str, description: str,
                priority: str = "Medium", origin: str = "Phone") -> str:
    log.info(f"create_case | subject={subject[:50]} | priority={priority}")
    result = sf.Case.create({
        "Subject":     subject,
        "Description": description,
        "Priority":    priority,
        "Origin":      origin,
        "Status":      "New"
    })
    case_id = result["id"]
    log.info(f"create_case | created | id={case_id}")
    return case_id

# ── UPDATE ───────────────────────────────────────────────────────

def update_case_with_summary(sf: Salesforce, case_id: str,
                              ai_summary: dict, call_id: str) -> bool:
    log.info(f"update_case_with_summary | case_id={case_id} | call_id={call_id}")

    description = f"""
=== AI-Generated Call Summary ===
Call ID: {call_id}

Issue: {ai_summary.get('issue', '')}

Resolution: {ai_summary.get('resolution', '')}

Next Best Action: {ai_summary.get('next_best_action', '')}

Sentiment: {ai_summary.get('sentiment', 'neutral')}
Escalation Required: {ai_summary.get('escalation_required', False)}
"""

    update_data = {
        "Description": description,
        "Status": "Working" if not ai_summary.get('escalation_required') else "Escalated",
        "Priority": "High" if ai_summary.get('escalation_required') else "Medium"
    }

    sf.Case.update(case_id, update_data)
    log.info(f"update_case_with_summary | updated | status={update_data['Status']} | priority={update_data['Priority']}")
    return True

def close_case(sf: Salesforce, case_id: str, resolution: str) -> bool:
    log.info(f"close_case | case_id={case_id}")
    sf.Case.update(case_id, {
        "Status":      "Closed",
        "Description": f"Resolution: {resolution}"
    })
    log.info(f"close_case | closed | case_id={case_id}")
    return True