# knowledge_base.py
# Policy documents grounding NBA suggestions
# These mirror the intent categories you configured in U-Assist

DOCUMENTS = [
    {
        "id": "POL-001",
        "intent": "cancellation",
        "title": "Cancellation Policy — Standard",
        "content": """
A customer requesting policy cancellation must be handled as follows:
1. Verify customer identity before processing any cancellation.
2. Inform the customer of the cancellation cooling-off period — 14 days from policy start.
3. If within cooling-off period, full refund is applicable with no penalties.
4. If outside cooling-off period, pro-rata refund applies based on unused premium.
5. Always offer a retention discount before processing — 20% for 3 months for standard tier, 30% for 6 months for premium tier.
6. If customer insists on cancellation, read the mandatory disclosure: "Cancelling your policy means you will no longer be covered for [product]. Are you sure you want to proceed?"
7. Log disposition code: CANC-FULL in CRM.
Next Best Action: Offer retention discount first. If declined, process cancellation and log CANC-FULL.
"""
    },
    {
        "id": "POL-002",
        "intent": "cancellation",
        "title": "Cancellation Policy — Mistaken Cancellation / Reinstatement",
        "content": """
If a customer reports their policy was cancelled in error:
1. Verify the cancellation date — reinstatement is possible within 30 days of cancellation.
2. Check for outstanding premium payments — customer must clear arrears before reinstatement.
3. If within 30 days and no arrears: reinstate immediately, no underwriting required.
4. If beyond 30 days: new application required, subject to underwriting review.
5. Inform customer: "Your policy can be reinstated today. There will be no gap in coverage if reinstated within 30 days."
6. Log disposition code: REINSTATE in CRM.
Next Best Action: Confirm cancellation date, check arrears, reinstate if eligible.
"""
    },
    {
        "id": "POL-003",
        "intent": "policy_inquiry",
        "title": "Policy Inquiry — Coverage Details",
        "content": """
When a customer asks about their policy coverage:
1. Pull policy details from CRM before responding — never quote coverage from memory.
2. Confirm which policy the customer is asking about if they hold multiple policies.
3. Key coverage details to confirm: sum insured, excess/deductible amount, renewal date, exclusions.
4. If customer asks about a specific claim scenario: "I can confirm your policy covers X. For a definitive answer on a specific claim, I recommend submitting a pre-claim inquiry."
5. Never guarantee claim outcomes — use language like "your policy includes coverage for" not "your claim will be approved."
6. Log disposition code: INQ-COV in CRM.
Next Best Action: Confirm policy details from CRM, provide coverage summary, offer to email a policy schedule.
"""
    },
    {
        "id": "POL-004",
        "intent": "policy_inquiry",
        "title": "Policy Inquiry — Renewal and Premium Changes",
        "content": """
When a customer asks about renewal or premium increases:
1. Pull the upcoming renewal notice details from CRM.
2. Explain premium change factors: claims history, age banding, market rate adjustments.
3. If premium increased by more than 15%: flag for retention review — customer is churn risk.
4. Offer loyalty discount if customer has been with the company for 3+ years: 10% loyalty discount applicable.
5. If customer wants to shop around: "I understand. Before you decide, can I check if you're eligible for our loyalty discount?"
6. Log disposition code: INQ-REN in CRM.
Next Best Action: If premium increase over 15% and 3+ year customer, apply loyalty discount proactively.
"""
    },
    {
        "id": "POL-005",
        "intent": "billing_dispute",
        "title": "Billing Dispute — Duplicate or Incorrect Charge",
        "content": """
When a customer reports an incorrect or duplicate charge:
1. Pull billing history from CRM — verify the charge before acknowledging the dispute.
2. If duplicate charge confirmed: process refund immediately, inform customer of 3-5 business day timeline.
3. If charge appears correct but customer disputes: escalate to billing team, do not dismiss the dispute.
4. For premium tier customers: expedite refund to 1-2 business days, flag account for priority review.
5. Log all disputes regardless of outcome — log disposition code: BILL-DISP in CRM.
6. After resolving: "I've processed your refund. You'll receive a confirmation email shortly."
Next Best Action: Verify charge in CRM first. If confirmed duplicate, refund immediately. Premium tier gets expedited timeline.
"""
    },
    {
        "id": "POL-006",
        "intent": "fraud_alert",
        "title": "Fraud Alert — Suspicious Transaction Protocol",
        "content": """
When a fraud alert is triggered during a call:
1. DO NOT confirm or deny any transaction details until identity is fully verified.
2. Enhanced identity verification required: full name, date of birth, policy number, AND one additional factor (mother's maiden name or memorable word).
3. If identity cannot be verified: "For your security, I'm unable to discuss account details. Please visit a branch with photo ID or call back from your registered number."
4. If fraud is confirmed: suspend the policy immediately, transfer to fraud team, do not process any transactions.
5. If customer becomes aggressive or threatening: follow escalation protocol — do not engage, transfer to senior agent.
6. Log disposition code: FRAUD-ALERT in CRM. This triggers automatic review within 24 hours.
Next Best Action: Enhanced identity verification first. Do not proceed with any transaction until identity confirmed.
"""
    },
    {
        "id": "POL-007",
        "intent": "cancellation",
        "title": "Cancellation Policy — Add-on / Rider Only",
        "content": """
When a customer wants to cancel an add-on or rider only (not the main policy):
1. Confirm which add-on the customer wants to remove — list all active add-ons from CRM.
2. Inform customer of the impact: "Removing [add-on] means you will no longer be covered for [specific benefit]."
3. Pro-rata refund applies for the unused portion of the add-on premium.
4. Main policy remains active — only the add-on is cancelled.
5. Cooling-off period applies to add-ons independently of the main policy.
6. Log disposition code: CANC-ADDON in CRM.
Next Best Action: Confirm which add-on, explain coverage impact, process partial cancellation, log CANC-ADDON.
"""
    },
]