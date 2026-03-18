ПРOMПТ ДЛЯ AI-АГЕНТА: Единая Мультимодаль + Fallback механизм

Role: Senior Backend Engineer

Context: Мы используем провайдера Chutes (OpenAI-compatible API), который хостит SOTA-модели на децентрализованных нодах. Из-за специфики сети ноды могут отвечать с ошибками (500, 502, timeouts). Нам нужен пуленепробиваемый механизм фолбеков (fallbacks) на резервные мультимодальные модели. Локальный GigaAM для распознавания аудио (ASR) остается.

Task: Обновить mod_llm.py и логику orchestrator.py для работы с каскадом мультимодальных моделей.

Requirements:

1. Модуль mod_llm.py:
Создай список моделей в порядке приоритета:
Python

CHUTES_BASE_URL = "https://llm.chutes.ai/v1"

MODELS_PRIORITY = [
    "qwen/Qwen3-VL-235B-A22B-Instruct", # Основная, самая умная
    "zai-org/GLM-4.6V",                 # Резерв 1
    "Qwen/Qwen2.5-VL-32B-Instruct"      # Резерв 2 (быстрая)
]

2. Оркестратор (core/orchestrator.py):
Модифицируй функцию вызова LLM (или process_universal_message):

    Аудио: Если в msg.attachments есть audio, прогоняем через audio_service и дописываем результат к тексту.

    Формирование Payload: Формируем массив content по стандарту OpenAI Vision. Если есть картинка: [{"type": "text", "text": msg.text}, {"type": "image_url", "image_url": {"url": image_url}}]. Если нет — просто текст.

    Fallback Цикл (CRITICAL):

        Реализуй цикл for model_id in MODELS_PRIORITY:

        Внутри цикла оберни асинхронный вызов к API (через openai.AsyncOpenAI или httpx) в try...except.

        Лови исключения (таймауты, ошибки API 5xx).

        Если запрос успешен — делай break и возвращай ответ.

        Если ошибка — логируй logger.warning(f"Модель {model_id} упала, переключаюсь на следующую...") и иди на следующую итерацию.

        Если цикл завершился и все модели упали, верни красивое сообщение пользователю: "Мои когнитивные центры сейчас перегружены. Дайте мне пару минут на восстановление связи."