# test_salesforce_auth.py
import asyncio
from salesforce_auth import get_salesforce_token

async def main():
    print("\n--- Testing Salesforce JWT Bearer auth ---\n")
    token_data = await get_salesforce_token()
    print(f"Access token: {token_data['access_token'][:40]}...")
    print(f"Instance URL: {token_data['instance_url']}")
    print("\nAuth successful ✅")

asyncio.run(main())