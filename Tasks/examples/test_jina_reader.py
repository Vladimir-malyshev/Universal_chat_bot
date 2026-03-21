import asyncio
import httpx
from duckduckgo_search import AsyncDDGS

async def fetch_jina_content(url: str, timeout: int = 15) -> str:
    """Fetch URL and parse content to markdown using Jina Reader API."""
    jina_url = f"https://r.jina.ai/{url}"
    print(f"[{url}] Fetching via Jina: {jina_url}")
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Jina Reader returns clean markdown representation of the page
            response = await client.get(jina_url)
            response.raise_for_status()
            text = response.text
            print(f"[{url}] Retrieved {len(text)} chars.")
            return text
    except Exception as e:
        print(f"[{url}] Failed to fetch: {e}")
        return f"Error: Could not retrieve content from {url}."

async def test_deep_search(query: str, num_results: int = 2):
    print(f"\n=== DEEP SEARCH TEST: '{query}' ===")
    
    print("1. Querying DuckDuckGo...")
    results = []
    
    try:
         async with AsyncDDGS() as ddgs:
             async for r in ddgs.text(query, max_results=num_results):
                 results.append(r)
    except Exception as e:
         print(f"DDG Search failed: {e}")
         return
         
    if not results:
        print("No results from DDG.")
        return
        
    print(f"Found {len(results)} URLs.")
    
    jina_results = []
    for r in results:
        print("Waiting 20 seconds to avoid rate limits...")
        await asyncio.sleep(20)
        res = await fetch_jina_content(r['href'])
        jina_results.append(res)
    
    print("\n--- SYNTHESIS ---")
    for i, (orig, content) in enumerate(zip(results, jina_results)):
        print(f"\nRESULT {i+1}: {orig['title']}")
        print(f"URL: {orig['href']}")
        print(f"Snippet (DDG): {orig['body']}")
        
        content_peek = content[:500].replace('\n', ' ') + "..." if len(content) > 500 else content
        print(f"Jina Markdown Peek ({len(content)} chars): {content_peek}")
        
    print("\nDeep search test complete.")

if __name__ == "__main__":
    test_queries = [
        "What are the latest updates to Python 3.13?",
    ]
    
    for q in test_queries:
        asyncio.run(test_deep_search(q, num_results=2))
