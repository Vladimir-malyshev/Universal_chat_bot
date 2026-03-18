import asyncio
import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_gigaam_pipeline():
    """Загрузка пайплайна GigaAM строго один раз при старте."""
    logger.info("Loading GigaAM v2_rnnt model into memory...")
    try:
        from gigaam import GigaAM
        return GigaAM(model_name="v2_rnnt")
    except ImportError:
        logger.error("gigaam package not installed.")
        return None

def _transcribe_audio_sync(file_path: str) -> str:
    model = get_gigaam_pipeline()
    if not model:
        logger.error("ASR Model is not loaded. Cannot transcribe.")
        return ""
    
    try:
        logger.info(f"Starting longform transcription for {file_path}")
        utterances = model.transcribe_longform(
            file_path, 
            vad_model="pyannote/segmentation-3.0"
        )
        if isinstance(utterances, list):
            text = " ".join(item.get("transcription", "") for item in utterances if "transcription" in item)
            return text.strip()
        return str(utterances)
    except Exception as e:
        logger.exception(f"Error in transcription: {e}")
        return ""

async def transcribe_audio_async(file_path: str) -> str:
    """Асинхронно вызывает тяжелый инференс ASR через asyncio.to_thread, не блокируя Event Loop."""
    try:
        text = await asyncio.to_thread(_transcribe_audio_sync, file_path)
        return text
    except Exception as e:
        logger.exception(f"asyncio.to_thread ASR error: {e}")
        return ""
