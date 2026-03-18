МАСТЕР-ПРОМПТ: Полная сборка ИИ-Ядра (Architecture, Logic, Env & Deps)

Role: Principal Python Engineer & System Architect

Context: Мы создаем омниканальное ИИ-ядро (FastAPI). Архитектура: Hexagonal (Ports & Adapters). Инструменты: GigaAM (локальный ASR), Chutes (LLM с фолбеками), Persona System (динамические промпты).

Task: Собрать финальную версию проекта, исключив все заглушки. Написать работающий код, настроить окружение и зависимости.

1. СТРОГИЕ ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ:

    Non-blocking: Тяжелый инференс GigaAM в audio_service.py СТРОГО через asyncio.to_thread.

    Fast Response: Вебхук в main.py возвращает 200 OK немедленно через BackgroundTasks.

    Fallback: В orchestrator.py реализовать цикл по списку MODELS_PRIORITY (Qwen3 VL -> GLM-4.6V -> Qwen2.5-VL) с обработкой ошибок API.

    Persona: Реальное чтение person.set и подгрузка instructions.txt + knowledge_base.txt из папки person/{name}/.

2. ФАЙЛ ЗАВИСИМОСТЕЙ (requirements.txt):
Сгенерируй полный список библиотек с актуальными версиями. Обязательно включи:

    fastapi, uvicorn[standard], httpx, pydantic-settings

    openai (для Chutes), python-dotenv, aiofiles

    torch, torchaudio (для GigaAM)

    pyannote.audio (для VAD в long-form ASR)

3. ФАЙЛ ОКРУЖЕНИЯ (.env.example):
Проверь шаблон файла .env со всеми необходимыми ключами. Используй двойные кавычки для значений. Включи:

    MAX_BOT_TOKEN=""

    MAX_API_URL="https://api.max.ru/v1/messages/send"

    CHUTES_API_KEY=""

    CHUTES_BASE_URL="https://llm.chutes.ai/v1"

    HF_TOKEN="" (для доступа к моделям pyannote на Hugging Face)

4. СТРУКТУРА КОДА (УБРАТЬ МОКИ):

    adapters/max_adapter.py: Реальная отправка через httpx.

    services/audio_service.py: Реальный GigaAM с методом transcribe_longform.

    services/persona_service.py: Реальное чтение файлов и кеширование персоны.

    core/orchestrator.py: Реальная сборка мультимодального промпта (текст + картинка) и логика перебора моделей при ошибках.