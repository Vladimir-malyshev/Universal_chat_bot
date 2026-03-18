# mod_llm.py

MODELS = [
    # --- Gemini Models ---
    {
        # Gemini 2.5 Pro — флагманская облачная модель Google.
        # Поддерживает reasoning (Deep Think), multimodal input (текст, изображения, аудио, видео, PDF),
        # search grounding (поиск Google) и function-calling.
        # Обрабатывает контекст до 1 000 000 токенов.
        # Идеальна для научных, технических, кодовых задач и глубокого анализа.
        "id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "family": "gemini",
        "FreeRPD": 100,
        "description": "Глубокий анализ, поиск, мультимодальность",
        "audio_support": True
    },
    {
        # Gemini 2.5 Flash — сбалансированная мощная облачная модель.
        # Поддерживает multimodal input (текст, изображения, аудио, видео),
        # reasoning и search grounding, function-calling.
        # Хороший выбор для диалогов, генерации идей и креативных задач.
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "family": "gemini",
        "FreeRPD": 250,
        "description": "Баланс скорости, качества, поиск",
        "audio_support": True
    },
    {
        # Gemini 2.5 Flash-Lite — самая быстрая и экономичная в семействе 2.5.
        # Поддерживает multimodal input (текст, изображения, аудио, видео, PDF),
        # reasoning (по умолчанию off, но можно включить) и search grounding.
        # Отлично подходит для массовых задач: перевод, классификация, суммаризация.
        "id": "gemini-2.5-flash-lite",
        "name": "Gemini 2.5 Flash-Lite",
        "family": "gemini",
        "FreeRPD": 1000,
        "description": "Очень быстрая, мультимодальная, с поиском",
        "audio_support": True
    },
    {
        # Gemini 2.0 Flash — предыдущая версия Flash.
        # Поддерживает текст, изображения, аудио, видео.
        # Есть grounding с Google Search, но reasoning и мультимодальность уступают версии 2.5.
        "id": "gemini-2.0-flash",
        "name": "Gemini 2.0 Flash",
        "family": "gemini",
        "FreeRPD": 200,
        "description": "Стабильная Flash 2.0, мультимодальность",
        "audio_support": True
    },
    {
        # Gemini 2.0 Flash-Lite — облегченное ядро той же модели.
        # Только аудио/текст/изображения, без глубокого reasoning.
        # Максимально упрощена ради скорости.
        "id": "gemini-2.0-flash-lite",
        "name": "Gemini 2.0 Flash-Lite",
        "family": "gemini",
        "FreeRPD": 200,
        "description": "Лёгкая версия Flash 2.0",
        "audio_support": True
    },

    # --- Gemma Models ---
    {
        # Gemma 3 27B IT — топовая открытая модель Gemma.
        # Поддерживает multimodal input (текст + изображения), long context до 128 000 токенов,
        # мощный reasoning и глубокий анализ.
        # Оптимальна для STEM-задач, анализа больших документов и сложных рассуждений.
        "id": "gemma-3-27b-it",
        "name": "Gemma 3 27B IT",
        "family": "gemma",
        "FreeRPD": 14400,
        "description": "Топ‑модель Gemma, мультимодальность, большой контекст",
        "audio_support": False
    },
    {
        # Gemma 3 12B IT — более компактная, но мощная модель.
        # Поддерживает multimodal input (текст + изображения),
        # способна решать большинство сложных задач с меньшими ресурсами.
        "id": "gemma-3-12b-it",
        "name": "Gemma 3 12B IT",
        "family": "gemma",
        "FreeRPD": 14400,
        "description": "Мощная, но быстрее 27B, мультимодальная",
        "audio_support": False
    },
    {
        # Gemma 3 4B IT — средняя модель в линейке Gemma 3.
        # Поддерживает текст и изображения, reasoning на базовом уровне.
        # Хороший баланс скорости, качества и мультимодальной поддержки.
        "id": "gemma-3-4b-it",
        "name": "Gemma 3 4B IT",
        "family": "gemma",
        "FreeRPD": 14400,
        "description": "Баланс скорости/качества, мультимодальность",
        "audio_support": False
    },
    {
        # Gemma 3n E4B IT — оптимизированная квантованная модель для локального или легкого облака.
        # Поддерживает текст и ограниченную мультимодальность (часто текст + изображения),
        # быстрее и легче в ресурсах, но с немного уменьшенным качеством.
        "id": "gemma-3n-e4b-it",
        "name": "Gemma 3n E4B IT",
        "family": "gemma",
        "FreeRPD": 14400,
        "description": "Локальная, быстрый баланс, мультимодальность",
        "audio_support": False
    },
    {
        # Gemma 3n E2B IT — самая лёгкая и быстрая модель Gemma для локального использования.
        # Поддерживает только текстовый ввод, минимальное reasoning.
        # Идеальна для мгновенных ответов на простые запросы с минимальными ресурсами.
        "id": "gemma-3n-e2b-it",
        "name": "Gemma 3n E2B IT",
        "family": "gemma",
        "FreeRPD": 14400,
        "description": "Самая лёгкая, только текст, простые ответы",
        "audio_support": False
    }
]

# Функция для получения информации о модели по ID
def get_model_info(model_id):
    """Получает информацию о модели по её ID."""
    return next((m for m in MODELS if m['id'] == model_id), None)

# Функция для получения семейства модели
def get_model_family(model_id):
    """Получает семейство модели ('gemini', 'gemma' или 'unknown')."""
    model_info = get_model_info(model_id)
    return model_info['family'] if model_info else 'unknown'

# Модель по умолчанию - первая из списка Gemini или_gemini_2.5_flash_lite_preview_06_17_
# Проверяем, существует ли модель по индексу 2
if len(MODELS) > 2 :
    DEFAULT_MODEL = MODELS[2]["id"] # gemini-2.5-flash-lite-preview-06-17
else:
    # Если нет, выбираем первую доступную модель Gemini
    default_model_info = next((m for m in MODELS if m['family'] == 'gemini'), None)
    DEFAULT_MODEL = default_model_info["id"] if default_model_info else MODELS[0]["id"]
