📋 МАСТЕР-ПРОМПТ: Разработка Омниканального ИИ-Ядра (FastAPI + GigaAM)

Role: Principal Python Architect & Lead Backend/ML Engineer

Context: Мы создаем омниканальную платформу ИИ-ассистента на базе FastAPI. Платформа должна уметь одновременно обслуживать несколько мессенджеров (сейчас MAX, в будущем Telegram, VK) из одной кодовой базы.
В корне проекта уже есть папка services/ (где лежит базовая логика LLM) и файл context_service.py (in-memory история диалогов).

Architectural Decisions & Constraints:

    Hexagonal Architecture: Слой Транспорта (Адаптеры мессенджеров) ничего не знает про LLM. Слой Бизнес-логики (Оркестратор) ничего не знает про мессенджеры.

    No Cross-Channel State: Контекст пользователей не склеивается. Пользователь в Telegram (tg_123) и в MAX (max_123) — это две разные сессии.

    Media IN, Text OUT: Бот принимает голосовые сообщения и изображения, но на выходе всегда генерирует ТОЛЬКО текст.

    Non-blocking ML (CRITICAL): Для распознавания аудио мы используем локальную SOTA-библиотеку GigaAM. Инференс PyTorch синхронный и тяжелый. Он обязан запускаться в отдельном потоке (через asyncio.to_thread), чтобы не заблокировать Event Loop сервера FastAPI. Загрузка весов в память должна происходить строго один раз при старте приложения (Singleton/lru_cache).

Task: Разработать базовую архитектуру платформы с нуля, следуя строгим шагам ниже.

Step-by-Step Implementation:

Шаг 1: Создание DTO (models/universal.py)
Создай Pydantic-модели:

    Attachment: поля type (строка: 'audio', 'image'), url (опционально), file_path (опционально, для локальных файлов).

    UniversalMessage: поля channel (строка, напр. 'max', 'tg'), user_id (строка, оригинальный ID из канала), text (опционально), attachments (список Attachment).

Шаг 2: Модуль Распознавания Голоса (services/audio_service.py)
Реализуй ASR через библиотеку GigaAM (от salute-developers).

    Используй метод transcribe_longform (модель v2_rnnt или подходящая для long-form). Учти использование VAD pyannote/segmentation-3.0 (требует переменную окружения HF_TOKEN).

    Загружай пайплайн в память только один раз.

    Напиши асинхронную функцию transcribe_audio_async(file_path: str) -> str. Внутри используй asyncio.to_thread() для вызова синхронного инференса.

    Обработка выхода: метод transcribe_longform возвращает список словарей utterances. Извлеки ключи transcription, склей их в одну строку через пробел и верни. Добавь try/except.

Шаг 3: Интерфейс Адаптера Каналов (adapters/base.py)
Создай абстрактный класс BaseChannelAdapter:

    Метод приёма сообщений от мессенджера (парсинг в UniversalMessage).

    Асинхронный метод send_text(user_id: str, text: str) для отправки ответа обратно пользователю.

Шаг 4: Адаптер для MAX (adapters/max_adapter.py)
Реализуй наследника BaseChannelAdapter для мессенджера MAX:

    APIRouter для приёма вебхуков.

    Парсинг JSON в UniversalMessage.

    Реализация send_text через httpx.AsyncClient к API MAX (url и токен бери из .env).

Шаг 5: Оркестратор (core/orchestrator.py)
Напиши асинхронную функцию process_universal_message(msg: UniversalMessage, adapter: BaseChannelAdapter):

    Формирует уникальный ID: session_id = f"{msg.channel}_{msg.user_id}".

    Если есть аудио-вложение -> вызывает await transcribe_audio_async(file_path) и добавляет текст к запросу.

    Достает историю из context_service по session_id.

    Вызывает логику LLM (импортируй заглушку или существующую функцию из services/), сохраняет новый контекст.

    Отправляет ответ: await adapter.send_text(msg.user_id, llm_reply).

Шаг 6: Точка входа (main.py)
Собери приложение FastAPI:

    Подключи роутер max_adapter.router.

    КРИТИЧНО: В эндпоинте вебхука немедленно возвращай HTTP 200 {"status": "ok"}, а вызов process_universal_message передавай в BackgroundTasks.