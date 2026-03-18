import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch

sys.path.append(os.getcwd())

from core.orchestrator import process_universal_message
from models.universal import UniversalMessage, Attachment
from adapters.max_adapter import max_adapter_instance

async def test_final_system():
    print("--- Тестирование Финальной Сборки Системы ---")
    
    # 1. Подготовка сообщения с картинкой и аудио
    msg = UniversalMessage(
        channel="max",
        user_id="user_123",
        text="Что на картинке и что я сказал?",
        attachments=[
            Attachment(type='image', url="https://example.com/image.jpg"),
            Attachment(type='audio', file_path="tests/sample_audio.wav")
        ]
    )

    # 2. Мокаем внешние зависимости
    with patch("core.orchestrator.AsyncOpenAI") as mock_openai, \
         patch("core.orchestrator.transcribe_audio_async") as mock_asr, \
         patch("adapters.max_adapter.httpx.AsyncClient") as mock_http:
        
        # Мокаем ASR
        mock_asr.return_value = "Привет, железный друг"
        
        # Мокаем LLM
        mock_llm_client = mock_openai.return_value
        mock_llm_client.chat.completions.create = AsyncMock(return_value=AsyncMock(
            choices=[AsyncMock(message=AsyncMock(content="На картинке пейзаж, и вы поздоровались."))]
        ))
        
        # Мокаем HTTP отправку (Max API)
        mock_http_client = mock_http.return_value.__aenter__.return_value
        mock_http_client.post = AsyncMock(return_value=AsyncMock(status_code=200))

        print("Запуск полной цепочки обработки...")
        await process_universal_message(msg, max_adapter_instance)
        
        print("\nПроверка вызовов:")
        print(f"ASR вызван: {mock_asr.called}")
        print(f"LLM вызван: {mock_llm_client.chat.completions.create.called}")
        print(f"MAX API вызван: {mock_http_client.post.called}")
        
        if mock_http_client.post.called:
            print("\nФинальная сборка работает корректно! ✅")

if __name__ == "__main__":
    asyncio.run(test_final_system())
