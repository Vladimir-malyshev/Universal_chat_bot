from abc import ABC, abstractmethod
from typing import Any
from models.universal import UniversalMessage

class BaseChannelAdapter(ABC):
    @abstractmethod
    def parse_message(self, raw_data: Any) -> UniversalMessage:
        """Converts incoming webhook payload to UniversalMessage DTO"""
        pass
    
    @abstractmethod
    async def send_text(self, user_id: str, text: str) -> None:
        """Sends text to user in specific channel"""
        pass
