import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch

sys.path.append(os.getcwd())

from adapters.telegram_adapter import telegram_adapter_instance
from models.universal import UniversalMessage

async def test_telegram_parsing():
    print("--- Тестирование Telegram Адаптера ---")
    
    # С имитированный Update от Telegram
    payload = {
        "update_id": 12345,
        "message": {
            "message_id": 1,
            "chat": {"id": 999},
            "from": {"id": 999},
            "text": "Тест ТГ",
            "photo": [{"file_id": "photo_id_1"}, {"file_id": "photo_id_max"}]
        }
    }

    # Мокаем get_file_url
    with patch.object(telegram_adapter_instance, 'get_file_url', new_callable=AsyncMock) as mock_url:
        mock_url.return_value = "https://api.telegram.org/file/bot123/photo.jpg"
        
        print("Парсинг сообщения...")
        msg = telegram_adapter_instance.parse_message(payload)
        
        print(f"Channel: {msg.channel}")
        print(f"User ID: {msg.user_id}")
        print(f"Attachments: {len(msg.attachments)}")
        
        if msg.channel == "telegram" and msg.user_id == "999":
            print("Базовый парсинг пройден! ✅")
            
        if msg.attachments and msg.attachments[0].type == "image":
             print("Парсинг фото (макс. размер) пройден! ✅")

if __name__ == "__main__":
    asyncio.run(test_telegram_parsing())
