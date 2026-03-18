# services/gemma_service.py
import logging
from datetime import datetime
from google import genai
from google.genai import types
from config import CURRENT_ROLE_SETTINGS # Импортируем настройки роли
from services.context_service import (
    get_context, add_to_context, get_chat_model,
    is_role_context_initialized, set_role_initialized
)
from utils.helpers import process_content

logger = logging.getLogger(__name__)

def _format_gemma_prompt(context_messages, current_user_message_parts, instructions_text=None, knowledge_base_text=None):
    """
    Форматирует промпт для модели Gemma согласно её спецификации.
    Использует <start_of_turn> и <end_of_turn>.
    """
    prompt_parts = []

    # 1. Добавляем инструкции, если они есть, в самом начале как первый пользовательский ввод
    # См. https://ai.google.dev/gemma/docs/core/prompt-structure#system_instructions
    # "Please provide system-level instructions directly in the initial user prompt..."
    if instructions_text:
        # Объединяем инструкции с первым пользовательским сообщением или создаем отдельное сообщение
        system_instruction_part = f"[ИНСТРУКЦИИ РОЛИ]\n{instructions_text}"
        prompt_parts.append(f"<start_of_turn>user\n{system_instruction_part}")
        # Базу знаний, если она есть, добавляем после инструкций в том же сообщении
        if knowledge_base_text:
             kb_part = f"\n\n[БАЗА ЗНАНИЙ РОЛИ]\n{knowledge_base_text}"
             prompt_parts[-1] += kb_part # Добавляем к последнему (инструкции) элементу
        prompt_parts[-1] += "\n<end_of_turn>" # Завершаем первый пользовательский ход
    else:
        # Если инструкций нет, базу знаний добавляем как первый пользовательский ввод
        if knowledge_base_text:
            kb_part = f"<start_of_turn>user\n[БАЗА ЗНАНИЙ РОЛИ]\n{knowledge_base_text}\n<end_of_turn>"
            prompt_parts.append(kb_part)
        # Если нет ни инструкций, ни базы знаний, ничего не добавляем в начало

    # 2. Добавляем историю контекста
    for msg in context_messages:
        role = msg['role']
        content = msg['content']
        # Gemma поддерживает только 'user' и 'model'
        gemma_role = 'user' if role == 'user' else 'model'
        prompt_parts.append(f"<start_of_turn>{gemma_role}\n{content}\n<end_of_turn>")

    # 3. Добавляем текущее сообщение пользователя
    # Объединяем все части текущего сообщения в одну строку
    current_user_text = ""
    for part in current_user_message_parts:
        if hasattr(part, 'text') and part.text is not None:
            current_user_text += part.text

        # Изображения и другие данные могут требовать специальной обработки
        # Пока предполагаем, что они уже в правильном формате для Contents
        # и будут добавлены отдельно в generate_content
    
    if current_user_text: # Добавляем только если есть текст
        prompt_parts.append(f"<start_of_turn>user\n{current_user_text}")

    # 4. Добавляем начало хода модели, чтобы модель знала, что нужно продолжить
    prompt_parts.append("<start_of_turn>model")

    # 5. Объединяем все части в один промпт
    full_prompt = "".join(prompt_parts)
    logger.debug(f"Сформированный промпт для Gemma:\n{full_prompt}")
    return full_prompt

def generate_response_gemma(chat_id: int, prompt: str, image_bytes: bytes = None) -> str:
    """
    Генерация ответа с помощью модели Gemma через Gemini API.
    
    Args:
        chat_id: ID чата
        prompt: Текст запроса
        image_bytes: Байты изображения (опционально)
    
    Returns:
        str: Ответ от модели
    """
    try:
        model_id = get_chat_model(chat_id)
        client = genai.Client()
        
        # --- Подготовка данных для промпта ---
        # 1. Получаем контекст
        context_messages = get_context(chat_id)
        
        # 2. Подготавливаем текущий ввод
        current_parts = [types.Part(text=prompt)]
        if image_bytes:
            # Используем Blob для передачи изображения
            image_part = types.Part(
                inline_data=types.Blob(
                    mime_type='image/jpeg', # Уточните MIME-тип, если он другой
                    data=image_bytes
                )
            )
            current_parts.append(image_part)

        # 3. Получаем настройки роли
        instructions_text = None
        knowledge_base_text = None
        if CURRENT_ROLE_SETTINGS.get('name'):
            logger.info(f"Используется роль: {CURRENT_ROLE_SETTINGS['name']} для модели Gemma")
            instructions_text = CURRENT_ROLE_SETTINGS.get('instructions')
            knowledge_base_text = CURRENT_ROLE_SETTINGS.get('knowledge_base')
            
            # Инициализация (добавление KB к первому запросу)
            if not is_role_context_initialized(chat_id):
                 logger.info(f"Инициализируем контекст для роли '{CURRENT_ROLE_SETTINGS['name']}' в чате {chat_id} (Gemma)")
                 # Помечаем инициализацию
                 set_role_initialized(chat_id)
                 # База знаний будет добавлена в промпт ниже
        else:
            logger.info("Используется стандартный режим для модели Gemma.")

        # --- Формирование промпта и contents ---
        # Для Gemma мы формируем специальный текстовый промпт
        # и передаем его как одну текстовую часть в Contents
        gemma_prompt = _format_gemma_prompt(
            context_messages, 
            current_parts, # Передаем все части, чтобы _format мог обработать текст
            instructions_text, 
            knowledge_base_text
        )
        
        # Contents для Gemma будет содержать:
        # 1. Сформированный текстовый промпт
        # 2. Опционально, изображение (если оно было)
        gemma_contents = [types.Part(text=gemma_prompt)]
        # Добавляем изображение, если оно было (оно не попадет в текстовый промпт)
        if image_bytes:
            # Убираем текстовую часть с промптом, если есть изображение,
            # и передаем промпт и изображение отдельно
            # См. примеры в https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api
            # Нужно передать и текст, и изображение в parts
            # Но промпт уже содержит текст, а изображение - отдельно.
            # Лучше передать промпт как текст, а изображение как отдельную часть.
            # Но API ожидает список parts. 
            # Давайте пересоздадим contents.
            gemma_contents = [types.Part(text=gemma_prompt)]
            if image_bytes:
                 # Добавляем изображение как отдельную часть
                 image_part = types.Part(
                    inline_data=types.Blob(
                        mime_type='image/jpeg',
                        data=image_bytes
                    )
                 )
                 gemma_contents.append(image_part) # Промпт + изображение

        # --- Подготовка конфигурации ---
        # ВАЖНО: Модели Gemma НЕ поддерживают system_instruction и tools!
        # См. https://ai.google.dev/gemma/docs/core/prompt-structure#unsupported_features
        config_kwargs = {
            # 'system_instruction' НЕ используется
            # 'tools' НЕ используется
            # Можно добавить другие параметры, если они поддерживаются
            # Например, температура, top_p и т.д.
        }

        # --- Генерация ответа ---
        logger.info(f"Отправляем запрос к модели Gemma '{model_id}'...")
        response = client.models.generate_content(
            model=model_id,
            contents=gemma_contents, # Передаем сформированные contents
            config=types.GenerateContentConfig(**config_kwargs)
        )
        
        # --- Обработка ответа ---
        try:
            if hasattr(response, 'text') and response.text is not None:
                gemma_raw_answer = response.text.strip()
            elif (
                hasattr(response, 'candidates') and response.candidates and
                hasattr(response.candidates[0], 'content') and
                response.candidates[0].content and
                hasattr(response.candidates[0].content, 'parts') and
                response.candidates[0].content.parts and
                response.candidates[0].content.parts[0].text is not None
            ):
                gemma_raw_answer = response.candidates[0].content.parts[0].text.strip()
            else:
                gemma_raw_answer = "Извините, не удалось сформулировать ответ (пустой ответ от модели Gemma)."
                logger.warning("Gemma вернула пустой или некорректный ответ.")
        except Exception as e:
            gemma_raw_answer = "Произошла ошибка при обработке ответа модели Gemma."
            logger.exception(f"Ошибка при извлечении текста из ответа Gemma: {e}")

        # === ДОБАВИТЬ ЭТИ СТРОКИ ===
        # Очищаем ответ перед отправкой пользователю
        import re
        # Создаем копию для пользователя, очищенную от тегов
        gemma_clean_answer = gemma_raw_answer
        # Удаляем все вхождения полных блоков тегов (<start_of_turn>...<end_of_turn>)
        gemma_clean_answer = re.sub(r"<start_of_turn>.*?<end_of_turn>\s*", "", gemma_clean_answer, flags=re.DOTALL)
        # На случай, если остались отдельные теги (например, <start_of_turn>model в конце промпта)
        gemma_clean_answer = gemma_clean_answer.replace("<start_of_turn>", "").replace("<end_of_turn>", "")
        # Также можно удалить возможные артефакты, например, "user\n" или "model\n" в начале/конце
        gemma_clean_answer = gemma_clean_answer.strip()
        # ===========================

        logger.info(f"Ответ от модели Gemma получен. Длина (сырого): {len(gemma_raw_answer)} символов.")

        # --- Сохранение в контекст ---
        # Сохраняем оригинальный запрос пользователя (без тегов)
        add_to_context(chat_id, 'user', prompt)
        # Сохраняем СЫРОЙ ответ модели (с тегами) в контекст, так как _format_gemma_prompt ожидает их
        add_to_context(chat_id, 'assistant', gemma_raw_answer) # <-- Сохраняем с тегами

        # Возвращаем ОЧИЩЕННЫЙ ответ пользователю
        return gemma_clean_answer # <-- Возвращаем без тегов
        
    except Exception as e:
        logger.error(f"Ошибка генерации ответа моделью Gemma: {e}", exc_info=True)
        return f"❌ Ошибка генерации (Gemma): {str(e)}"
