import logging
import asyncio
from typing import List, Dict, Any
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

async def search_web(query: str, max_results: int = 5) -> str:
    """
    Выполняет поиск в интернете через DuckDuckGo и возвращает краткую сводку.
    """
    try:
        logger.info(f"Searching web for: {query}")
        results = []
        
        # DDGS() в новых версиях поддерживает контекстный менеджер
        with DDGS() as ddgs:
            ddgs_gen = ddgs.text(query, max_results=max_results)
            for r in ddgs_gen:
                results.append(f"Title: {r['title']}\nSnippet: {r['body']}\nLink: {r['href']}\n")
        
        if not results:
            return "Поиск не дал результатов."
        
        return "\n---\n".join(results)
    except Exception as e:
        logger.error(f"Error during web search: {e}")
        return f"Ошибка при поиске в интернете: {e}"

# Схема инструмента для OpenAI / Chutes API
SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Поиск в интернете через DuckDuckGo. Используй ТОЛЬКО для запросов о текущих ценах, актуальных новостях, конкурентах или событиях 2025-2026 годов. Не используй для ответов на общие вопросы, которые можно решить без доступа к сети.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", 
                    "description": "Точный поисковый запрос (например, 'курс биткоина сегодня' или 'цены на удобрения 2026')"
                }
            },
            "required": ["query"]
        }
    }
}

AVAILABLE_TOOLS = [SEARCH_TOOL_SCHEMA]

async def execute_tool(name: str, args: Dict[str, Any]) -> str:
    """Выполняет инструмент по имени."""
    if name == "search_web":
        return await search_web(args.get("query", ""))
    return f"Инструмент {name} не найден."
