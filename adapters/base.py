from abc import ABC, abstractmethod
from typing import Any, Optional
from models.universal import UniversalMessage

class BaseChannelAdapter(ABC):
    @abstractmethod
    def parse_message(self, raw_data: Any) -> UniversalMessage:
        """Converts incoming webhook payload to UniversalMessage DTO"""
        pass
    
    @abstractmethod
    async def send_text(self, user_id: str, text: str) -> Optional[str]:
        """Sends text to user in specific channel. Returns message_id if successful."""
        pass

    @abstractmethod
    async def edit_text(self, user_id: str, message_id: str, text: str) -> bool:
        """Edits existing message. Returns True if successful."""
        pass
