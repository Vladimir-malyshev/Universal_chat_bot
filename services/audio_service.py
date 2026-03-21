# TODO: В будущем заменить локальную загрузку модели на вызов внешнего сервиса (speech-service)
import asyncio
import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_gigaam_pipeline():
    """Загрузка пайплайна GigaAM v3 строго один раз при старте."""
    model_id = "v3_e2e_ctc"
    logger.info(f"Loading GigaAM {model_id} model into memory...")
    try:
        import gigaam
        # В V3 используем load_model вместо прямого создания класса
        return gigaam.load_model(model_id)
    except Exception as e:
        logger.error(f"Failed to load GigaAM model: {e}")
        return None

def _transcribe_audio_sync(file_path: str) -> str:
    """Синхронная транскрибация файла."""
    model = get_gigaam_pipeline()
    if not model:
        logger.error("ASR Model is not loaded. Cannot transcribe.")
        return ""
    
    try:
        logger.info(f"Transcribing {file_path} using GigaAM v3")
        # Метод transcribe в v3 возвращает текст с пунктуацией
        text = model.transcribe(file_path)
        return text.strip() if text else ""
    except Exception as e:
        logger.exception(f"Error in transcription: {e}")
        return ""

async def transcribe_audio_async(file_path: str) -> str:
    """Асинхронная обертка для транскрибации."""
    try:
        return await asyncio.to_thread(_transcribe_audio_sync, file_path)
    except Exception as e:
        logger.exception(f"ASR async error: {e}")
        return ""
