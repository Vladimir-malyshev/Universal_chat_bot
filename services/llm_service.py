import os
import asyncio
import logging
import json
from openai import AsyncOpenAI
from google import genai
from google.genai import types
from google.genai.errors import APIError

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
OPENROUTER_MODEL = "openrouter/free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

class DummyToolCallFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

class DummyToolCall:
    def __init__(self, id, function):
        self.id = id
        self.function = function

class DummyMessage:
    def __init__(self, content, tool_calls=None, role="assistant"):
        self.content = content
        self.tool_calls = tool_calls
        self.role = role

def convert_openai_tools_to_gemini(tools: list) -> list:
    """Конвертирует OpenAI tools в Google GenAI format."""
    if not tools:
        return []
    gemini_tools = []
    for tool in tools:
        if tool.get("type") == "function":
            fn = tool["function"]
            props = fn.get("parameters", {}).get("properties", {})
            req = fn.get("parameters", {}).get("required", [])
            
            gemini_props = {}
            for k, v in props.items():
                gemini_props[k] = {"type": v.get("type", "STRING").upper(), "description": v.get("description", "")}
                
            func_decl = types.FunctionDeclaration(
                name=fn["name"],
                description=fn.get("description", ""),
                parameters={
                    "type": "OBJECT",
                    "properties": gemini_props,
                    "required": req
                } if props else None
            )
            gemini_tools.append(types.Tool(function_declarations=[func_decl]))
    return gemini_tools

async def call_llm(messages: list, attachments: list = None, tools: list = None) -> any:
    """
    Вызов LLM с поддержкой мультимодальности и Tool Calling.
    Сначала пробует gemini-3.1-flash-lite-preview.
    При ошибке перегрузки пробует еще 2 раза.
    Если не получилось - фолбэк на openrouter/free.
    """
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if gemini_api_key:
        try:
            logger.info(f"Attempting Gemini API with {GEMINI_MODEL}")
            res = await _call_gemini(messages, attachments, tools, gemini_api_key)
            if res:
                return res
        except Exception as e:
            logger.warning(f"All Gemini attempts failed: {e}. Falling back to OpenRouter.")
    else:
        logger.warning("GOOGLE_API_KEY not found. Skipping Gemini.")

    logger.info(f"Attempting OpenRouter API with {OPENROUTER_MODEL}")
    return await _call_openrouter(messages, attachments, tools)

async def _call_gemini(messages: list, attachments: list, tools: list, api_key: str):
    client = genai.Client(api_key=api_key)
    
    contents = []
    system_instruction = ""
    
    for i, m in enumerate(messages):
        role = m.get("role") if isinstance(m, dict) else m.role
        content = m.get("content") if isinstance(m, dict) else m.content

        # Handle tool call messages
        if role == "tool":
            continue # In Gemini, tool results should be structured, but let's map them simply for now
            # Actually, to properly handle tools we need types.Content(role='function', parts=[...])
            # But the user logic stores them as system messages or tool messages. Let's just append as is.
        
        if role == "system":
            system_instruction += str(content) + "\n"
        elif role == "user":
            parts = []
            if isinstance(content, list):
                for p in content:
                    if p.get("type") == "text":
                        parts.append(types.Part.from_text(text=p["text"]))
                    elif p.get("type") == "image_url":
                        import base64
                        url = p["image_url"]["url"]
                        if url.startswith("data:"):
                            parts.append(_base64_to_part(url))
            else:
                parts.append(types.Part.from_text(text=str(content)))
            
            # Attachments for the last message
            is_last_user_message = (i == len(messages) - 1) or all((m_next.get("role") if isinstance(m_next, dict) else m_next.role) != "user" for m_next in messages[i+1:])
            
            if attachments and is_last_user_message:
                for att in attachments:
                    if hasattr(att, 'type') and att.type == 'image':
                        if hasattr(att, 'url') and att.url and att.url.startswith("data:"):
                             parts.append(_base64_to_part(att.url))
                        elif hasattr(att, 'file_path') and att.file_path:
                             from services.audio_utils import get_file_base64
                             b64 = get_file_base64(att.file_path)
                             if b64: parts.append(_base64_to_part(f"data:image/jpeg;base64,{b64}"))

            contents.append(types.Content(role="user", parts=parts))
        elif role == "assistant":
            contents.append(types.Content(role="model", parts=[types.Part.from_text(text=str(content) if content else "")]))

    config_args = {
        "thinking_config": types.ThinkingConfig(include_thoughts=True, thinking_level='HIGH')
    }
    if system_instruction:
        config_args["system_instruction"] = system_instruction
    if tools:
        config_args["tools"] = convert_openai_tools_to_gemini(tools)

    config = types.GenerateContentConfig(**config_args)

    for attempt in range(3):
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=GEMINI_MODEL,
                contents=contents,
                config=config
            )
            
            content_text = ""
            tool_calls = []
            
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.thought:
                        logger.debug(f"Gemini Thoughts: {part.text}")
                    elif part.function_call:
                        import uuid
                        call_id = f"call_{uuid.uuid4().hex[:8]}"
                        fn_args = json.dumps(type(part.function_call.args)(part.function_call.args)) if hasattr(part.function_call.args, '__dict__') else json.dumps(part.function_call.args)
                        if isinstance(part.function_call.args, dict): fn_args = json.dumps(part.function_call.args)
                        
                        tool_calls.append(DummyToolCall(
                            id=call_id,
                            function=DummyToolCallFunction(
                                name=part.function_call.name,
                                arguments=fn_args
                            )
                        ))
                    elif part.text:
                        content_text += part.text

            return DummyMessage(
                content=content_text.strip() if content_text else None,
                tool_calls=tool_calls if tool_calls else None
            )

        except Exception as e:
            if attempt < 2 and ("429" in str(e) or "503" in str(e) or "overload" in str(e).lower() or isinstance(e, APIError)):
                logger.warning(f"Gemini API overload (attempt {attempt+1}/3): {e}. Retrying in 10s...")
                await asyncio.sleep(10)
            else:
                raise e

def _base64_to_part(data_url: str):
    import base64
    mime_type = data_url.split(";")[0].split(":")[1]
    b64_data = data_url.split(",")[1]
    image_bytes = base64.b64decode(b64_data)
    return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

async def _call_openrouter(messages, attachments, tools):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not found in env.")
        return None

    # Мультимодальная обработка для OpenRouter (OpenAI совместимая)
    proc_messages = list(messages)
    if attachments:
        for i in range(len(proc_messages) - 1, -1, -1):
            m = proc_messages[i]
            role = m.get("role") if isinstance(m, dict) else m.role
            content = m.get("content") if isinstance(m, dict) else m.content
            
            if role == "user" and isinstance(content, str):
                user_content = [{"type": "text", "text": content}]
                
                for att in attachments:
                    if hasattr(att, 'type') and att.type == 'image':
                        if hasattr(att, 'url') and att.url:
                            user_content.append({"type": "image_url", "image_url": {"url": att.url}})
                
                if isinstance(m, dict):
                    proc_messages[i] = {**m, "content": user_content}
                else:
                    m.content = user_content
                break

    client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
    kwargs = {
        "model": OPENROUTER_MODEL,
        "messages": proc_messages,
        "timeout": 45.0
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    
    try:
        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message
    except Exception as e:
        logger.error(f"OpenRouter Fallback failed: {e}")
        return None
