import logging
import os
from openai import AsyncOpenAI
from models.universal import UniversalMessage
from adapters.base import BaseChannelAdapter
from services.audio_service import transcribe_audio_async
from services.context_service import get_context, add_to_context
from services.persona_service import persona_service
from mod_llm import CHUTES_BASE_URL, MODELS_PRIORITY

logger = logging.getLogger(__name__)

async def call_llm(context: list, system_prompt: str, attachments: list = None) -> str:
    """
    Вызов LLM с каскадным Fallback механизмом. 
    Поддерживает мультимодальные вложения (Vision).
    """
    api_key = os.getenv("CHUTES_API_KEY")
    if not api_key:
        logger.error("CHUTES_API_KEY not found in environment.")
        return "Ошибка конфигурации: отсутствует API ключ."

    client = AsyncOpenAI(base_url=CHUTES_BASE_URL, api_key=api_key)
    
    # Формируем контент для последнего сообщения (мультимодальный)
    user_text = context[-1]["content"] if context else ""
    messages = [{"role": "system", "content": system_prompt}]
    
    # Добавляем историю (кроме последнего сообщения, которое мы сейчас пересоберем)
    for msg in context[:-1]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Собираем последнее сообщение пользователя
    user_content = [{"type": "text", "text": user_text}]
    
    if attachments:
        for att in attachments:
            if att.type == 'image' and (att.url or att.file_path):
                img_url = att.url if att.url else f"data:image/jpeg;base64,{att.file_path}" # Это упрощение
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": img_url}
                })
    
    messages.append({"role": "user", "content": user_content})

    # Цикл Fallback (CRITICAL)
    for model_id in MODELS_PRIORITY:
        try:
            logger.info(f"Attempting LLM call with model: {model_id}")
            response = await client.chat.completions.create(
                model=model_id,
                messages=messages,
                timeout=30.0
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Модель {model_id} упала или таймаут: {e}, переключаюсь на следующую...")
            continue
    
    return "Мои когнитивные центры сейчас перегружены. Дайте мне пару минут на восстановление связи."

async def process_universal_message(msg: UniversalMessage, adapter: BaseChannelAdapter):
    try:
        session_id = f"{msg.channel}_{msg.user_id}"
        logger.info(f"Processing message for session: {session_id}")

        # 1. Системный промпт
        system_prompt = persona_service.get_full_system_prompt()

        # 2. Обработка аудио
        if msg.attachments:
            for att in msg.attachments:
                if att.type == 'audio' and att.file_path:
                    logger.info(f"Transcribing audio from: {att.file_path}")
                    transcript = await transcribe_audio_async(att.file_path)
                    if transcript:
                        if msg.text:
                            msg.text += f"\n[Распознанное аудио]: {transcript}"
                        else:
                            msg.text = transcript

        if not msg.text and not any(a.type == 'image' for a in msg.attachments):
            logger.warning(f"No content to process for session {session_id}")
            return

        # 3. Контекст
        add_to_context(session_id, "user", msg.text or "")
        context = get_context(session_id)

        # 4. Вызов LLM (Cascade Fallback)
        llm_reply = await call_llm(context, system_prompt, msg.attachments)

        # 5. Сохранение и ответ
        add_to_context(session_id, "assistant", llm_reply)
        await adapter.send_text(msg.user_id, llm_reply)

    except Exception as e:
        logger.exception(f"Error processing universal message: {e}")
