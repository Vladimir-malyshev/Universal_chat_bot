# models/chat_models.py
"""Модели данных для хранения состояния чата"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
# Импортируем get_default_model и get_model_info для инициализации по умолчанию
from mod_llm import get_default_model, get_model_info

# --- Вспомогательная функция для получения информации о модели по умолчанию ---
def _get_default_model_info() -> Dict[str, Any]:
    """
    Получает информацию о модели, используемой по умолчанию.
    Возвращает копию словаря из MODELS или базовый словарь, если модель не найдена.
    """
    default_id = get_default_model()
    default_info = get_model_info(default_id)
    if default_info:
        # Возвращаем копию, чтобы избежать неожиданного изменения оригинала
        return default_info.copy() 
    else:
        # На случай, если get_default_model() указывает на несуществующую модель
        return {
            "id": default_id,
            "name": "Unknown Model",
            "family": "unknown",
            "input_token_limit": 32768, 
        }
# --- Конец вспомогательной функции ---

@dataclass
class ChatMessage:
    """Модель сообщения в чате"""
    role: str  # 'user' или 'assistant'
    content: str
    timestamp: datetime

# --- Обновлённый ChatSettings с корректной инициализацией по умолчанию ---
@dataclass
class ChatSettings:
    """Модель настроек чата"""
    max_history: int = 100
    context_ttl: int = 12000
    # current_model теперь инициализируется информацией о DEFAULT_MODEL
    current_model: Dict[str, Any] = field(default_factory=_get_default_model_info)
    voice_mode: bool = False
# --- Конец обновлённого ChatSettings ---

@dataclass
class ChatContext:
    """Модель контекста чата"""
    messages: List[ChatMessage]
    settings: ChatSettings
