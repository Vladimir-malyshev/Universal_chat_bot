ПРOMПТ ДЛЯ AI-АГЕНТА: Рефакторинг mod_llm.py (Переход на Chutes)

Role: Senior Backend Engineer

Context: Мы очищаем технический долг в модуле mod_llm.py. Старый файл перегружен комментариями, неиспользуемыми параметрами (вроде FreeRPD) и устаревшими моделями. Мы полностью переходим на провайдера Chutes (OpenAI-compatible API).

Task: Полностью переписать файл mod_llm.py, сделав его минималистичным, читаемым и удобным для поддержки.

Requirements:

    Clean Structure: Удали все старые словари (Gemini, Groq, OpenRouter и т.д.).

    Simplified Schema: Используй простую и понятную структуру словаря для моделей. Оставь только самое необходимое:

        id: строковый ID модели в системе Chutes (например, "deepseek-ai/DeepSeek-R1" или "meta-llama/Llama-3-70b-instruct").

        name: человекочитаемое название.

        context_length: лимит токенов (int).

        vision_support: bool (может ли модель принимать картинки).

    Chutes Configuration: Добавь в начало файла константы для подключения к Chutes (чтобы Оркестратор потом мог их импортировать):

        CHUTES_BASE_URL = "https://api.chutes.ai/v1" (или актуальный URL из их доки).

        Напиши комментарий, что CHUTES_API_KEY должен браться из .env.

    Helper Functions: Напиши две лаконичные функции с Type Hints:

        get_model_info(model_id: str) -> dict | None

        get_default_model() -> str (пусть возвращает первую модель из списка).

    No Bloat: Никаких огромных абзацев с описаниями. Код должен помещаться на одном экране. Добавь в список 3-4 актуальные SOTA-модели из Chutes для примера.