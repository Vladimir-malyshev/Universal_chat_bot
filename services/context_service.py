# services/context_service.py
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from config import MAX_HISTORY, CONTEXT_TIMEOUT
from mod_llm import DEFAULT_MODEL

logger = logging.getLogger(__name__)

# Хранилища контекста и настроек
chat_contexts = defaultdict(list)
chat_settings = defaultdict(dict)
chat_models = defaultdict(lambda: DEFAULT_MODEL)
voice_states = defaultdict(bool)  # Словарь для отслеживания режима дублирования

def get_chat_settings(chat_id: int) -> dict:
    """Получение настроек чата"""
    return chat_settings.get(chat_id, {})

def set_max_history(chat_id: int, value: int):
    """Установка максимальной глубины истории"""
    chat_settings[chat_id]['max_history'] = value

def set_context_ttl(chat_id: int, value: int):
    """Установка времени жизни контекста"""
    chat_settings[chat_id]['context_ttl'] = value

def set_role_initialized(chat_id: int):
    """Помечает, что контекст для роли в этом чате инициализирован"""
    chat_settings[chat_id]['role_initialized'] = True

def is_role_context_initialized(chat_id: int) -> bool:
    """Проверяет, был ли инициализирован контекст для роли в этом чате"""
    return chat_settings[chat_id].get('role_initialized', False)

def get_context(chat_id: int) -> list:
    """
    Получение контекста диалога для чата с учетом настроек
    
    Args:
        chat_id: ID чата
    
    Returns:
        list: Отфильтрованный контекст
    """
    # Инициализируем пустой список если chat_id отсутствует
    if chat_id not in chat_contexts:
        chat_contexts[chat_id] = []
    
    now = datetime.now()
    settings = get_chat_settings(chat_id)
    max_history = settings.get('max_history', MAX_HISTORY)
    context_ttl = settings.get('context_ttl', CONTEXT_TIMEOUT)
    
    # Фильтруем сообщения по времени и ограничению истории
    filtered_context = [
        m for m in chat_contexts[chat_id]
        if now - m['timestamp'] < timedelta(seconds=context_ttl)
    ]
    
    # Возвращаем последние max_history сообщений
    return filtered_context[-max_history:] if max_history else filtered_context

def add_to_context(chat_id: int, role: str, content: str):
    """
    Добавление сообщения в контекст диалога
    
    Args:
        chat_id: ID чата
        role: Роль (user/assistant)
        content: Содержание сообщения
    """
    # Инициализируем пустой список если chat_id отсутствует
    if chat_id not in chat_contexts:
        chat_contexts[chat_id] = []
    
    # Добавляем сообщение с текущим временем
    chat_contexts[chat_id].append({
        'role': role,
        'content': content,
        'timestamp': datetime.now(),
    })

def clear_chat_history(chat_id: int):
    """Очистка истории диалога для чата"""
    chat_contexts[chat_id] = []

def get_chat_model(chat_id: int) -> str:
    """Получение модели для конкретного чата"""
    return chat_models[chat_id]

def set_chat_model(chat_id: int, model_id: str):
    """Установка модели для конкретного чата"""
    chat_models[chat_id] = model_id

def get_voice_mode(chat_id: int) -> bool:
    """Получение состояния голосового режима"""
    return voice_states[chat_id]

def toggle_voice_mode(chat_id: int) -> bool:
    """Переключение голосового режима"""
    voice_states[chat_id] = not voice_states[chat_id]
    return voice_states[chat_id]
