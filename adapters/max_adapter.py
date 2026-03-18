import os
import logging
from typing import Any
import httpx
from fastapi import APIRouter, Request, BackgroundTasks

from models.universal import UniversalMessage, Attachment
from adapters.base import BaseChannelAdapter

logger = logging.getLogger(__name__)

router = APIRouter()

class MaxAdapter(BaseChannelAdapter):
    def __init__(self):
        self.max_url = os.getenv("MAX_API_URL", "https://api.max-messenger.com")
        self.max_token = os.getenv("MAX_API_TOKEN", "")

    def parse_message(self, payload: Any) -> UniversalMessage:
        user_id = payload.get("user_id", "unknown")
        text = payload.get("text")
        
        attachments = []
        for att in payload.get("attachments", []):
            attachments.append(Attachment(
                type=att.get("type", "audio"),
                url=att.get("url"),
                file_path=att.get("file_path")
            ))
            
        return UniversalMessage(
            channel="max",
            user_id=str(user_id),
            text=text,
            attachments=attachments
        )

    async def send_text(self, user_id: str, text: str) -> None:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.max_token}"}
            payload_data = {
                "user_id": user_id, 
                "text": text
            }
            try:
                logger.info(f"Sending to MAX user {user_id}: {text[:50]}...")
                response = await client.post(
                    self.max_url, 
                    json=payload_data, 
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Failed to send to MAX: {e}")

max_adapter_instance = MaxAdapter()

@router.post("/webhook/max")
async def max_webhook(request: Request, background_tasks: BackgroundTasks):
    from core.orchestrator import process_universal_message
    
    try:
        payload = await request.json()
        msg = max_adapter_instance.parse_message(payload)
        background_tasks.add_task(process_universal_message, msg, max_adapter_instance)
    except Exception as e:
        logger.error(f"Error parsing MAX webhook payload: {e}")
        
    return {"status": "ok"}
