# test_llm.py
import asyncio
from llm import generate_call_summary, generate_call_summary_structured, generate_call_summary_cot


SAMPLE_TRANSCRIPT = """
Agent: Thank you for calling billing support, this is Priya. How can I help?
Customer: Hi, I've been charged twice for my subscription this month.
          I need this fixed immediately, it's really frustrating.
Agent: I completely understand, I'm sorry about that.
       Let me pull up your account right now.
Agent: I can see the duplicate charge. I'm going to process a full refund
       for the second charge — you'll see it in 3-5 business days.
Customer: Okay, thank you. I hope this doesn't happen again.
Agent: I've also added a note to your account to flag for our billing team.
       Is there anything else I can help you with?
Customer: No, that's all. Thanks.
"""

ESCALATION_TRANSCRIPT = """
Agent: Thank you for calling support, this is James. How can I help?
Customer: I have been waiting THREE WEEKS for my refund and nobody has helped me.
          I want to speak to a manager RIGHT NOW. This is completely unacceptable.
Agent: I sincerely apologise for the wait. Let me check your account.
Agent: I can see the refund request but it appears to be stuck in processing.
       I don't have the authority to override this — I need to escalate this to my supervisor.
Customer: Finally. Yes please do that.
"""

AMBIGUOUS_TRANSCRIPT = """
Agent: Thank you for calling, this is Priya. How can I help?
Customer: Hi, I wanted to cancel my subscription actually.
Agent: I'm sorry to hear that. Can I ask what's prompting you to cancel today?
Customer: It's just too expensive for what I'm getting.
Agent: I completely understand. We do have a loyalty discount I can apply —
       it would reduce your bill by 20% for the next 6 months.
Customer: Hmm. I wasn't expecting that.
Agent: A lot of customers find it really helps. Want me to apply it now?
Customer: I guess so. Sure, go ahead.
Agent: Done! You're all set with the discount.
Customer: Okay. Thanks I suppose.
"""

async def main():
    print("\n=== Test 1: Direct prompting on ambiguous call ===")
    summary1 = await generate_call_summary_structured(AMBIGUOUS_TRANSCRIPT)
    for key, value in summary1.items():
        print(f"  {key}: {value}")

    print("\n=== Test 2: Chain-of-thought on same call ===")
    summary2 = await generate_call_summary_cot(AMBIGUOUS_TRANSCRIPT)
    for key, value in summary2.items():
        print(f"  {key}: {value}")

    print("\n=== Token cost comparison ===")
    print("  Direct:  ~370 tokens")
    print("  CoT:     ~700-900 tokens (more reasoning = more cost)")
    print("  Question: is the quality improvement worth the cost?")

asyncio.run(main())