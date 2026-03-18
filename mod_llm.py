# mod_llm.py
"""
Конфигурация LLM моделей через провайдера Chutes (OpenAI-compatible).
CHUTES_API_KEY должен быть определен в .env.
"""

CHUTES_BASE_URL = "https://llm.chutes.ai/v1"

# Список моделей в порядке приоритета для Fallback-механизма
MODELS_PRIORITY = [
    "zai-org/GLM-4.6V",                       # Основная (VL + Tools работают стабильно)
    "Qwen/Qwen3-VL-235B-A22B-Instruct",         # Резерв (могут быть проблемы с Tools на Chutes)
    "Qwen/Qwen2.5-VL-32B-Instruct"            # Резерв 2 (быстрая)
]

# Для обратной совместимости или детальной информации (опционально)
MODELS = [
    {
        "id": "zai-org/GLM-4.6V",
        "name": "GLM-4.6V (Main)",
        "context_length": 131072,
        "vision_support": True
    },
    {
        "id": "Qwen/Qwen3-VL-235B-A22B-Instruct",
        "name": "Qwen3 VL (Fallback 1)",
        "context_length": 131072,
        "vision_support": True
    },
    {
        "id": "Qwen/Qwen2.5-VL-32B-Instruct",
        "name": "Qwen2.5 VL (Fallback 2)",
        "context_length": 32768,
        "vision_support": True
    }
]

def get_model_info(model_id: str) -> dict | None:
    """Возвращает информацию о модели по её ID."""
    return next((m for m in MODELS if m["id"] == model_id), None)

def get_default_model() -> str:
    """Возвращает ID первой модели в приоритетном списке."""
    return MODELS_PRIORITY[0]
