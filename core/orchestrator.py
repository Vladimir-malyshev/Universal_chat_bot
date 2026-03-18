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
        import re
        import json
        
        # Паттерн для перехвата XML-вызовов (GLM/Qwen на Chutes)
        # Пример: <toolcall>searchweb <argkey>query</argkey> <argvalue>...</argvalue> </tool_call>
        tool_regex = r"<toolcall>(?P<name>.*?)<argkey>.*?</argkey>\s*<argvalue>(?P<value>.*?)</argvalue>.*?</tool_?call>"
        
        search_msg_id = None
        actions = []
        
        # Собираем официальные вызовы
        if response_msg.tool_calls:
            for tc in response_msg.tool_calls:
                actions.append({
                    "type": "official",
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": json.loads(tc.function.arguments)
                })
        
        # Собираем Regex-вызовы из текста
        content_text = response_msg.content or ""
        matches = list(re.finditer(tool_regex, content_text, re.DOTALL | re.IGNORECASE))
        for match in matches:
            actions.append({
                "type": "regex",
                "name": match.group("name").strip(),
                "args": {"query": match.group("value").strip()},
                "raw_text": match.group(0)
            })

        if actions:
            logger.info(f"Detected {len(actions)} tool actions (Official: {len(response_msg.tool_calls or [])}, Regex: {len(matches)})")
            
            # UX: Индикация поиска
            search_msg_id = await adapter.send_text(
                msg.user_id, 
                "🔍 <i>Ищу актуальные данные в интернете...</i>"
            )
            
            # Добавляем сообщение ассистента в историю
            # Если это был только Regex-вызов, OpenAI API может не принять его как assistant message без content
            messages.append(response_msg)
            
            for action in actions:
                f_name = action["name"]
                f_args = action["args"]
                
                # Выполнение инструмента
                result = await execute_tool(f_name, f_args)
                
                # Добавляем результат в историю
                if action["type"] == "official":
                    logger.info(f"Adding official tool result for {f_name} to context.")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": action["id"],
                        "name": f_name,
                        "content": result
                    })
                else:
                    # Для Regex-вызовов добавляем как системное сообщение для четкого разделения контекста
                    logger.info(f"Adding regex tool result for {f_name} as SYSTEM message.")
                    messages.append({
                        "role": "system",
                        "content": f"[ОБЪЕКТИВНЫЕ ДАННЫЕ ИЗ ИНТЕРНЕТА ({f_name})]:\n{result}\n\nИнструкция: Используй эти данные как единственный источник истины для ответа. Если данных нет или там ошибка, честно скажи об этом пользователю."
                    })
            
            # Логируем итоговый набор сообщений (только роли и длину контента для безопасности)
            for i, m in enumerate(messages):
                try:
                    role = m.role if hasattr(m, 'role') else m.get('role')
                    content = m.content if hasattr(m, 'content') else m.get('content', '')
                    logger.debug(f"Message {i} | Role: {role} | Length: {len(str(content))}")
                except Exception as log_err:
                    logger.warning(f"Failed to log message {i}: {log_err}")

            # Второй вызов LLM (финальный ответ)
            response_msg = await call_llm(messages, attachments=None, tools=None)

        if not response_msg or (not response_msg.content and not response_msg.tool_calls):
             await adapter.send_text(msg.user_id, "Не удалось сформировать ответ после поиска.")
             return

        llm_reply = response_msg.content or ""
        
        # Очистка финального ответа от возможных остаточных XML-тегов (галлюцинации)
        llm_reply = re.sub(tool_regex, "", llm_reply, flags=re.DOTALL | re.IGNORECASE).strip()

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
