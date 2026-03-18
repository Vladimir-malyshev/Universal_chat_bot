# services/gemini_service.py
"""Сервис для генерации ответов моделями семейства Gemini."""
import logging
from datetime import datetime
from google import genai
from google.genai import types
# Импортируем настройки роли из config и функции из context_service
from config import CURRENT_ROLE_SETTINGS
from services.context_service import (
    get_context, add_to_context, get_chat_model,
    is_role_context_initialized, set_role_initialized
)
from utils.helpers import process_content

logger = logging.getLogger(__name__)

def generate_response_gemini(chat_id: int, prompt: str, image_bytes: bytes = None) -> str:
    """Генерация ответа с помощью модели Gemini."""
    try:
        model_id = get_chat_model(chat_id)
        client = genai.Client()

        # Формируем контекст
        ctx = []
        for m in get_context(chat_id):
            processed_content = process_content(m['content'])
            ctx.append({
                'role': 'user' if m['role'] == 'user' else 'model',
                'parts': processed_content
            })

        # Подготавливаем текущий ввод
        current_parts = [types.Part(text=prompt)]
        if image_bytes:
            logger.debug(f"[DEBUG] Размер image_bytes: {len(image_bytes)} байт")
            image_part = types.Part(
                inline_data=types.Blob(
                    mime_type='image/jpeg',
                    data=image_bytes
                )
            )
            current_parts.append(image_part)

        # Настройка роли (если задана)
        if CURRENT_ROLE_SETTINGS.get('name'):
            logger.info(f"Используется роль: {CURRENT_ROLE_SETTINGS['name']}")
            if not is_role_context_initialized(chat_id):
                logger.info(f"Инициализируем контекст для роли '{CURRENT_ROLE_SETTINGS['name']}' в чате {chat_id}")
                if CURRENT_ROLE_SETTINGS.get('knowledge_base'):
                    kb_text = f"[БАЗА ЗНАНИЙ РОЛИ {CURRENT_ROLE_SETTINGS['name']}]\n{CURRENT_ROLE_SETTINGS['knowledge_base']}"
                    current_parts.insert(0, types.Part(text=kb_text))
                    logger.info(f"База знаний роли добавлена к первому запросу в чате {chat_id}")
                    logger.debug(f"СОДЕРЖАНИЕ БАЗЫ ЗНАНИЙ:\n{CURRENT_ROLE_SETTINGS['knowledge_base'][:500]}...")
                set_role_initialized(chat_id)
        else:
            logger.info("Используется стандартный режим.")

        current_input = {'role': 'user', 'parts': current_parts}
        contents = ctx + [current_input]

        # === ЛОГИРОВАНИЕ ВСЕГО КОНТЕКСТА ===
        logger.debug(f"ПОЛНЫЙ КОНТЕКСТ (contents) для чата {chat_id} (для Gemini):")
        for i, msg in enumerate(contents):
            role = msg.get('role', 'unknown')
            parts = msg.get('parts', [])
            logger.debug(f"  [{i}] Роль: {role}")
            for j, part in enumerate(parts):
                try:
                    if hasattr(part, 'text') and part.text is not None:
                        text_preview = part.text[:300] + "..." if len(part.text) > 300 else part.text
                        logger.debug(f"      Часть {j}: TEXT ({len(part.text)} символов) -> {text_preview}")
                    elif hasattr(part, 'inline_data') and part.inline_data:
                        data = getattr(part.inline_data, 'data', None)
                        size = len(data) if data else 0
                        mime_type = getattr(part.inline_data, 'mime_type', 'unknown')
                        logger.debug(f"      Часть {j}: INLINE_DATA (mime_type: {mime_type}, size: {size} bytes)")
                    else:
                        logger.debug(f"      Часть {j}: НЕИЗВЕСТНЫЙ ТИП ({type(part)})")
                except Exception as log_error:
                    logger.warning(f"⚠️ Ошибка при логгировании части {j}: {log_error}")

        # Конфигурация запроса
        config_kwargs = {
            'system_instruction': f"Сегодня - {datetime.now().strftime('%d.%m.%Y')}",
            'tools': [types.Tool(google_search=types.GoogleSearch())]
        }

        if CURRENT_ROLE_SETTINGS.get('name'):
            instructions_text = CURRENT_ROLE_SETTINGS.get('instructions', '')
            if instructions_text:
                config_kwargs['system_instruction'] += f"\n\n{instructions_text}"

        logger.debug(f"SYSTEM INSTRUCTION для чата {chat_id} (для Gemini):\n{config_kwargs['system_instruction']}")

        # Отправка запроса
        logger.info(f"Отправляем запрос к модели Gemini '{model_id}'...")
        response = client.models.generate_content(
            model=model_id,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs)
        )

        # Извлечение ответа
        if hasattr(response, 'text') and response.text:
            gemini_answer = response.text
        elif response.candidates and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            gemini_answer = getattr(part, 'text', '') or "Извините, не удалось сформулировать ответ."
        else:
            gemini_answer = "Извините, не удалось сформулировать ответ."

        # Сохраняем историю
        add_to_context(chat_id, 'user', prompt)
        add_to_context(chat_id, 'assistant', gemini_answer)

        logger.info(f"Ответ от модели Gemini получен. Длина: {len(gemini_answer)} символов.")
        return gemini_answer

    except Exception as e:
        logger.error(f"Ошибка генерации ответа (Gemini): {e}", exc_info=True)
        return f"❌ Ошибка генерации (Gemini): {str(e)}"
