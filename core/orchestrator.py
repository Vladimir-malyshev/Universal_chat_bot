import logging
from models.universal import UniversalMessage
from adapters.base import BaseChannelAdapter
from services.audio_service import transcribe_audio_async
from services.context_service import get_context, add_to_context
from services.persona_service import persona_service

logger = logging.getLogger(__name__)

async def call_llm(context: list, system_prompt: str) -> str:
    """Заглушка для генерации ответа LLM. Принимает system_prompt."""
    # В будущем здесь будет реальный вызов LLM с системным промптом
    if not context:
        return "Привет! Я универсальный ИИ-ассистент."
    
    last_msg = context[-1]["content"]
    logger.info(f"LLM called with system_prompt (length {len(system_prompt)})")
    return f"Вы сказали: {last_msg}. Я работаю под ролью: {persona_service.current_persona_name}."

async def process_universal_message(msg: UniversalMessage, adapter: BaseChannelAdapter):
    try:
        session_id = f"{msg.channel}_{msg.user_id}"
        logger.info(f"Processing message for session: {session_id}")

        # Получаем текущий системный промпт из сервиса персон
        system_prompt = persona_service.get_full_system_prompt()

        # Обработка аудио-вложений с помощью GigaAM ASR
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

        if not msg.text:
            logger.warning(f"No text to process for session {session_id} after audio transcription.")
            return

        # Достаем историю
        add_to_context(session_id, "user", msg.text)
        context = get_context(session_id)

        # Вызов логики LLM с системным промптом
        llm_reply = await call_llm(context, system_prompt)

        # Сохраняем новый контекст
        add_to_context(session_id, "assistant", llm_reply)

        # Отправляем ответ
        await adapter.send_text(msg.user_id, llm_reply)

    except Exception as e:
        logger.exception(f"Error processing universal message: {e}")
