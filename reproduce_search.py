from services.tools import search_web
import asyncio
import logging

# Setup logging to see our new logs
logging.basicConfig(level=logging.INFO)

async def test_search():
    query = "текущая цена нефти Brent WTI сегодня 2025"
    print(f"Searching for: {query}")
    result = await search_web(query)
    print("\nRESULT:")
    print("-" * 30)
    print(result[:500] + "...")
    print("-" * 30)

if __name__ == "__main__":
    asyncio.run(test_search())
