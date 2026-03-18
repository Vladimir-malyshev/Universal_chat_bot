import asyncio
import sys
import os

# Добавляем корневой путь проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tools import search_web

async def test_search():
    print("Testing DuckDuckGo search...")
    query = "цена биткоина сегодня 2026"
    result = await search_web(query)
    
    print(f"\nQUERY: {query}")
    print("-" * 30)
    print(result[:1000]) # Печатаем первые 1000 символов
    print("-" * 30)
    
    if "Title:" in result and "Link:" in result:
        print("\n✅ Search tool works correctly!")
    else:
        print("\n❌ Search tool failed or returned no results.")

if __name__ == "__main__":
    asyncio.run(test_search())
