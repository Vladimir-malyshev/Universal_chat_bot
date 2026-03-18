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

async def call_llm(messages: list, attachments: list = None, tools: list = None) -> any:
    """
    Вызов LLM с поддержкой Vision и Tool Calling. 
    Возвращает объект сообщения (с текстом или tool_calls).
    """
    api_key = os.getenv("CHUTES_API_KEY")
    if not api_key:
        logger.error("CHUTES_API_KEY not found in environment.")
        return None

    client = AsyncOpenAI(base_url=CHUTES_BASE_URL, api_key=api_key)
    
    # Мультимодальная обработка для последнего сообщения (если есть вложения)
    if attachments:
        # Находим последнее сообщение от пользователя в списке
        for i in range(len(messages) - 1, -1, -1):
            if messages[i]["role"] == "user" and isinstance(messages[i]["content"], str):
                text = messages[i]["content"]
                user_content = [{"type": "text", "text": text}]
                
                for att in attachments:
                    if att.type == 'image' and (att.url or att.file_path):
                        img_url = att.url
                        user_content.append({
                            "type": "image_url",
                            "image_url": {"url": img_url}
                        })
                
                messages[i]["content"] = user_content
                break

    # Цикл Fallback (CRITICAL)
    for model_id in MODELS_PRIORITY:
        try:
            logger.info(f"Attempting LLM call with model: {model_id}")
            
            kwargs = {
                "model": model_id,
                "messages": messages,
                "timeout": 45.0
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            try:
                response = await client.chat.completions.create(**kwargs)
                return response.choices[0].message
            except Exception as e:
                if "tool choice requires" in str(e).lower() and "auto" in str(e).lower():
                    logger.warning(f"Model {model_id} does not support explicit tool_choice='auto' on Chutes. Retrying without it.")
                    kwargs.pop("tool_choice", None)
                    response = await client.chat.completions.create(**kwargs)
                    return response.choices[0].message
                raise e
        except Exception as e:
            logger.warning(f"Модель {model_id} упала или таймаут: {e}, переключаюсь на следующую...")
            continue
    
    return None

async def process_universal_message(msg: UniversalMessage, adapter: BaseChannelAdapter):
    temp_files = []
    try:
        session_id = f"{msg.channel}_{msg.user_id}"
        logger.info(f"Processing message for session: {session_id}")

        # 1. Системный промпт
        system_prompt = persona_service.get_full_system_prompt()

        # 2. Обработка медиа-вложений (Audio/Vision)
        if msg.attachments:
            from services.audio_utils import convert_ogg_to_wav, generate_unique_filename, cleanup_files, get_file_base64
            for att in msg.attachments:
                # АУДИО
                if att.type == 'audio' and att.file_path and os.path.exists(att.file_path):
                    ogg_path = att.file_path
                    temp_files.append(ogg_path)
                    
                    wav_path = generate_unique_filename("wav")
                    temp_files.append(wav_path)
                    
                    logger.info(f"Converting {ogg_path} to {wav_path}")
                    if convert_ogg_to_wav(ogg_path, wav_path):
                        transcript = await transcribe_audio_async(wav_path)
                        if transcript:
                            logger.info(f"Transcription successful: {transcript[:50]}...")
                            if msg.text:
                                msg.text += f"\n[Распознанное аудио]: {transcript}"
                            else:
                                msg.text = transcript

                # ИЗОБРАЖЕНИЯ (Vision)
                elif att.type == 'image' and att.file_path and os.path.exists(att.file_path):
                    img_path = att.file_path
                    temp_files.append(img_path)
                    
                    logger.info(f"Encoding image {img_path} to Base64")
                    b64_data = get_file_base64(img_path)
                    if b64_data:
                        # Подменяем URL на Data URI для LLM
                        att.url = f"data:image/jpeg;base64,{b64_data}"

        if not msg.text and not any(a.type == 'image' for a in msg.attachments):
            logger.warning(f"No content to process for session {session_id}")
            return

        # 3. Контекст и Сообщения для LLM
        context = get_context(session_id)
        messages = [{"role": "system", "content": system_prompt}]
        for m in context:
            messages.append({"role": m["role"], "content": m["content"]})
        
        # Добавляем само текущее сообщение пользователя в конец
        messages.append({"role": "user", "content": msg.text or ""})

        # 4. Первый вызов LLM (с инструментами)
        from services.tools import AVAILABLE_TOOLS, execute_tool
        
        response_msg = await call_llm(messages, msg.attachments, tools=AVAILABLE_TOOLS)
        
        if not response_msg:
            await adapter.send_text(msg.user_id, "Мои когнитивные центры сейчас перегружены. Попробуйте чуть позже.")
            return

        # 5. Обработка Tool Calling (Double-Hop)
        search_msg_id = None
        if response_msg.tool_calls:
            logger.info(f"LLM requested tool calls: {len(response_msg.tool_calls)}")
            
            # UX: Индикация поиска
            search_msg_id = await adapter.send_text(
                msg.user_id, 
                "🔍 <i>Ищу актуальные данные в интернете...</i>"
            )
            
            messages.append(response_msg) # Добавляем сообщение ассистента с tool_calls в историю
            
            for tool_call in response_msg.tool_calls:
                import json
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                # Выполнение инструмента
                result = await execute_tool(function_name, arguments)
                
                # Добавляем результат в историю
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": result
                })
            
            # Второй вызов LLM (финальный ответ)
            response_msg = await call_llm(messages, attachments=None, tools=None)

        if not response_msg or not response_msg.content:
             await adapter.send_text(msg.user_id, "Не удалось сформировать ответ после поиска.")
             return

        llm_reply = response_msg.content

        # 6. Сохранение и ответ
        add_to_context(session_id, "user", msg.text or "") # Сохраняем как текст
        add_to_context(session_id, "assistant", llm_reply)
        
        # UX: Редактируем "Ищу..." или отправляем новое сообщение
        if search_msg_id:
            success = await adapter.edit_text(msg.user_id, search_msg_id, llm_reply)
            if not success:
                logger.warning(f"Failed to edit search message {search_msg_id}, sending new one.")
                await adapter.send_text(msg.user_id, llm_reply)
        else:
            await adapter.send_text(msg.user_id, llm_reply)

    except Exception as e:
        logger.exception(f"Error processing universal message: {e}")
    finally:
        # 7. Гарантированная очистка временных файлов
        if temp_files:
            try:
                from services.audio_utils import cleanup_files
                cleanup_files(*temp_files)
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")
