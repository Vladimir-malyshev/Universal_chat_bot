import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_tg():
    token = os.getenv("TG_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/getMe"
    print(f"Testing connection to: {url}")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            print(f"Body: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_tg())
