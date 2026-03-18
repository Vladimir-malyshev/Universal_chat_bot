# models/chat_models.py
"""Модели данных для хранения состояния чата"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class ChatMessage:
    """Модель сообщения в чате"""
    role: str  # 'user' или 'assistant'
    content: str
    timestamp: datetime

@dataclass
class ChatSettings:
    """Модель настроек чата"""
    max_history: int = 100
    context_ttl: int = 12000
    current_model: str = "gemini-2.5-flash"
    voice_mode: bool = False

@dataclass
class ChatContext:
    """Модель контекста чата"""
    messages: List[ChatMessage]
    settings: ChatSettings