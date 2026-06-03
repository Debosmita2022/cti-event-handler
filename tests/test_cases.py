import asyncio
from salesforce_cases import (
    get_sf_connection, get_case_by_id, get_cases_by_phone,
    get_open_cases, create_case, update_case_with_summary, close_case
)

def main():
    sf = get_sf_connection()
    print("\n=== Test 1: Get open cases ===")
    cases = get_open_cases(sf)
    for c in cases:
        print(f"  {c['CaseNumber']} | {c['Status']} | {c['Subject'][:50]}")

    print("\n=== Test 2: Get case by ID ===")
    if cases:
        first_id = cases[0]['Id']
        case = get_case_by_id(sf, first_id)
        print(f"  Found: {case['CaseNumber']} — {case['Subject']}")

    print("\n=== Test 3: Create a new case ===")
    new_id = create_case(
        sf,
        subject="Customer billed twice — duplicate charge",
        description="Customer called reporting duplicate charge on billing statement.",
        priority="High"
    )
    print(f"  Created case ID: {new_id}")

    print("\n=== Test 4: Update case with AI summary ===")
    ai_summary = {
        "issue": "Customer charged twice for subscription this month",
        "resolution": "Agent processed full refund for duplicate charge",
        "next_best_action": "Follow up in 5 days to confirm refund received",
        "sentiment": "negative",
        "escalation_required": False
    }
    update_case_with_summary(sf, new_id, ai_summary, "CALL-20250602-001")
    print(f"  Updated case {new_id} with AI summary")

    print("\n=== Test 5: Close the case ===")
    close_case(sf, new_id, "Refund processed. Customer satisfied.")
    print(f"  Closed case {new_id}")

    print("\n=== Verify in Salesforce ===")
    final = get_case_by_id(sf, new_id)
    print(f"  Status: {final['Status']}")
    print(f"  Priority: {final['Priority']}")

main()