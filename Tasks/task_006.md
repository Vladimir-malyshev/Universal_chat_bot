ПРOMПТ ДЛЯ AI-АГЕНТА: Добавление Telegram Адаптера

Role: Senior Backend Engineer

Context: В нашем омниканальном ИИ-ядре (FastAPI) клиент задерживает выдачу токена для мессенджера MAX. Чтобы протестировать ядро (GigaAM + Chutes LLM + Persona), мы оперативно добавляем поддержку Telegram. Архитектура остается прежней: адаптер конвертирует входящий вебхук в UniversalMessage и передает в Оркестратор.

Task: Написать adapters/telegram_adapter.py и подключить его в main.py.

Requirements:

1. Модуль adapters/telegram_adapter.py:

    Наследуется от BaseChannelAdapter.

    Должен содержать APIRouter с эндпоинтом /webhook/telegram для приема POST-запросов от Telegram API.

    Парсинг входящего JSON (Update object):

        Извлечь user_id (message.from.id или message.chat.id).

        Извлечь text.

        Голосовые (Voice): Если есть message.voice, реализовать логику получения file_path через https://api.telegram.org/bot{token}/getFile?file_id=... и формирования полного URL для скачивания файла. Добавить в UniversalMessage как Attachment с типом audio.

        Картинки (Photo): Аналогично для message.photo (брать фото максимального размера, последний элемент массива).

    Реализовать асинхронный метод send_text(user_id, text) через httpx.AsyncClient (https://api.telegram.org/bot{token}/sendMessage).

2. Интеграция в main.py:

    Подключить роутер Telegram адаптера в основное приложение FastAPI.

    Как и с адаптером MAX, вызов process_universal_message должен происходить строго через BackgroundTasks, а вебхук должен моментально возвращать 200 OK.

3. Окружение:

    Использовать токен из .env -> TG_BOT_TOKEN.