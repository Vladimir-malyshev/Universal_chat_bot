import os
import logging
import httpx
from typing import Any, Optional
from fastapi import APIRouter, Request, BackgroundTasks

from models.universal import UniversalMessage, Attachment
from adapters.base import BaseChannelAdapter

logger = logging.getLogger(__name__)

router = APIRouter()

class TelegramAdapter(BaseChannelAdapter):
    def __init__(self):
        self.token = os.getenv("TG_BOT_TOKEN", "")
        self.api_base = f"https://api.telegram.org/bot{self.token}"

    def parse_message(self, payload: Any) -> Optional[UniversalMessage]:
        """Парсит Update от Telegram."""
        message = payload.get("message")
        if not message:
            return None

        chat_id = message.get("chat", {}).get("id")
        user_id = str(chat_id)
        text = message.get("text")
        attachments = []

        # 1. Обработка голосовых сообщений
        if "voice" in message:
            voice = message["voice"]
            file_id = voice["file_id"]
            attachments.append(Attachment(
                type="audio",
                url=f"{self.api_base}/getFile?file_id={file_id}", # Это промежуточный шаг
                file_path=file_id # Используем как ID файла
            ))

        # 2. Обработка фотографий (берем самую большую)
        if "photo" in message:
            photos = message["photo"]
            best_photo = photos[-1]
            file_id = best_photo["file_id"]
            attachments.append(Attachment(
                type="image",
                url=f"{self.api_base}/getFile?file_id={file_id}",
                file_path=file_id
            ))

        return UniversalMessage(
            channel="telegram",
            user_id=user_id,
            text=text,
            attachments=attachments
        )

    async def send_text(self, user_id: str, text: str) -> None:
        """Отправка сообщения через Telegram API."""
        url = f"{self.api_base}/sendMessage"
        payload = {
            "chat_id": user_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Failed to send Telegram message to {user_id}: {e}")

    async def get_file_url(self, file_id: str) -> Optional[str]:
        """Получает прямую ссылку на файл в Telegram."""
        url = f"{self.api_base}/getFile?file_id={file_id}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                data = response.json()
                if data.get("ok"):
                    file_path = data["result"]["file_path"]
                    return f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            except Exception as e:
                logger.error(f"Error getting Telegram file path: {e}")
        return None

telegram_adapter_instance = TelegramAdapter()

@router.post("/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    from core.orchestrator import process_universal_message
    
    try:
        payload = await request.json()
        msg = telegram_adapter_instance.parse_message(payload)
        
        if msg:
            # Пре-процессинг ссылок на файлы (критично для Telegram)
            for att in msg.attachments:
                if att.file_path:
                   real_url = await telegram_adapter_instance.get_file_url(att.file_path)
                   if real_url:
                       att.url = real_url

            background_tasks.add_task(process_universal_message, msg, telegram_adapter_instance)
            
    except Exception as e:
        logger.error(f"Error in Telegram webhook: {e}")
        
    return {"status": "ok"}
