
# 10 diverse transcripts covering different call types

TRANSCRIPTS = [
    {
        "id": "T01",
        "type": "billing_duplicate",
        "expected_sentiment": "negative",
        "expected_escalation": False,
        "transcript": """
Agent: Billing support, this is Priya. How can I help?
Customer: I was charged twice this month. I need a refund.
Agent: I can see the duplicate charge. Refunding now — 3-5 business days.
Customer: Thank you, that was quick.
Agent: Is there anything else I can help with?
Customer: No, that's all. Thanks.
"""
    },
    {
        "id": "T02",
        "type": "cancellation_retained",
        "expected_sentiment": "neutral",
        "expected_escalation": False,
        "transcript": """
Agent: Hi, this is James. How can I help today?
Customer: I want to cancel my subscription. It's too expensive.
Agent: I understand. Can I offer you a 30% discount for 3 months?
Customer: I suppose that works. Fine.
Agent: Done! Discount applied.
Customer: Okay. Thanks.
"""
    },
    {
        "id": "T03",
        "type": "escalation_required",
        "expected_sentiment": "negative",
        "expected_escalation": True,
        "transcript": """
Agent: Support line, how can I help?
Customer: I have been waiting 4 weeks for my refund. FOUR WEEKS.
          I want a manager NOW. This is absolutely unacceptable.
Agent: I'm so sorry. I've checked and the refund is stuck.
       I don't have authority to override it. I need to escalate.
Customer: Yes, please do that immediately.
"""
    },
    {
        "id": "T04",
        "type": "technical_resolved",
        "expected_sentiment": "positive",
        "expected_escalation": False,
        "transcript": """
Agent: Technical support, this is Sarah. How can I help?
Customer: My app keeps crashing when I try to log in.
Agent: Let me check your account. Can you try clearing the cache?
Customer: Oh! That worked. It's loading now.
Agent: Great! That's a common fix. Let me know if it happens again.
Customer: Perfect, thank you so much!
"""
    },
    {
        "id": "T05",
        "type": "partial_resolution",
        "expected_sentiment": "neutral",
        "expected_escalation": False,
        "transcript": """
Agent: Hi, billing support. How can I help?
Customer: My invoice has three errors on it.
Agent: I can see two of them and I've corrected those.
       The third one needs our billing team to review — 2-3 days.
Customer: So it's not fully fixed yet?
Agent: Not yet, but we're working on it.
Customer: Okay, I guess I'll wait.
"""
    },
    {
        "id": "T06",
        "type": "repeat_caller",
        "expected_sentiment": "negative",
        "expected_escalation": True,
        "transcript": """
Agent: Support, this is Mark. How can I help?
Customer: This is my FIFTH call about the same issue.
          My account has been locked for two weeks.
Agent: I'm very sorry. Let me check.
Agent: I can see previous tickets but the fix didn't apply.
       I'll escalate this to tier 2 support immediately.
Customer: I hope this actually gets fixed this time.
"""
    },
    {
        "id": "T07",
        "type": "positive_upsell",
        "expected_sentiment": "positive",
        "expected_escalation": False,
        "transcript": """
Agent: Hi, this is Lisa. How can I help today?
Customer: I wanted to ask about upgrading my plan.
Agent: Great! The premium plan adds 5 users and priority support.
       It's only $20 more per month.
Customer: That sounds perfect for my team. Let's do it.
Agent: Upgrade complete! You'll see the new features immediately.
Customer: Excellent, thank you!
"""
    },
    {
        "id": "T08",
        "type": "unresolved_complaint",
        "expected_sentiment": "negative",
        "expected_escalation": True,
        "transcript": """
Agent: Customer service, how can I help?
Customer: Your service has been down for 6 hours and we're losing money.
Agent: I understand and I apologise. Our engineers are working on it.
Customer: That's not good enough. We need compensation.
Agent: I can offer a credit for today's downtime.
Customer: That doesn't cover our losses. I want to speak to someone senior.
Agent: I'll escalate you to our enterprise team right away.
"""
    },
    {
        "id": "T09",
        "type": "confused_customer",
        "expected_sentiment": "neutral",
        "expected_escalation": False,
        "transcript": """
Agent: Hi, this is Tom. How can I help?
Customer: I got an email saying my payment failed but money left my account.
Agent: Let me check. The payment did go through — the email was a system error.
       Your account is active and in good standing.
Customer: Oh thank goodness. So I don't need to do anything?
Agent: Nothing at all. The email was sent in error.
Customer: That's a relief. Thanks for clarifying.
"""
    },
    {
        "id": "T10",
        "type": "churn_risk_retained",
        "expected_sentiment": "neutral",
        "expected_escalation": False,
        "transcript": """
Agent: Hi, this is Priya. How can I help today?
Customer: Honestly I'm thinking of switching to your competitor.
          They're offering me a better deal.
Agent: I'd hate to lose you. Can I ask what they're offering?
Customer: 20% cheaper with the same features.
Agent: I can match that and add priority support at no extra cost.
Customer: Hm. That's actually better. Okay, I'll stay.
Agent: Wonderful! I've applied the discount. You're all set.
Customer: Thanks. I'll give it another shot.
"""
    }
]