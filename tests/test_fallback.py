import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch

# Добавляем корневую папку в path для импортов
sys.path.append(os.getcwd())

from core.orchestrator import call_llm
from mod_llm import MODELS_PRIORITY

async def test_fallback():
    print("--- Тестирование Fallback Механизма ---")
    
    context = [{"role": "user", "content": "Привет, как дела?"}]
    system_prompt = "Ты ассистент."
    
    os.environ["CHUTES_API_KEY"] = "test_key"

    # Мокаем AsyncOpenAI
    with patch("core.orchestrator.AsyncOpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        
        # Настраиваем поведение: первая модель падает (timeout), вторая возвращает успех
        mock_client.chat.completions.create = AsyncMock(side_effect=[
            Exception("Timeout on first node"),
            AsyncMock(choices=[AsyncMock(message=AsyncMock(content="Ответ от второй модели"))])
        ])

        print(f"Запуск call_llm с ожидаемым падением первого вызова...")
        reply = await call_llm(context, system_prompt)
        
        print(f"Результат: {reply}")
        if "второй модели" in reply:
            print("Fallback отработал корректно! ✅")
        else:
            print("Ошибка в логике fallback! ❌")

        # Тест полного падения
        print("\nТест полного падения всех моделей...")
        mock_client.chat.completions.create = AsyncMock(side_effect=[Exception("Fail")] * len(MODELS_PRIORITY))
        reply_fail = await call_llm(context, system_prompt)
        print(f"Результат при полном падении: {reply_fail}")
        if "перегружены" in reply_fail:
             print("Красивое сообщение об ошибке возвращено! ✅")

if __name__ == "__main__":
    asyncio.run(test_fallback())
