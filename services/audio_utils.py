import os
import uuid
import httpx
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

TEMP_DIR = "temp_audio"

def ensure_temp_dir():
    """Создает временную директорию, если она не существует."""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        logger.info(f"Created temp directory: {TEMP_DIR}")

def generate_unique_filename(extension: str) -> str:
    """Генерирует уникальное имя файла с заданным расширением."""
    ensure_temp_dir()
    return os.path.join(TEMP_DIR, f"{uuid.uuid4()}.{extension}")

async def download_file(url: str, save_path: str) -> bool:
    """Асинхронно скачивает файл по URL."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(response.content)
        logger.info(f"Downloaded file to {save_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download file from {url}: {e}")
        return False

def convert_ogg_to_wav(ogg_path: str, wav_path: str) -> bool:
    """
    Конвертирует OGG/Opus в WAV (16kHz, mono) с помощью ffmpeg.
    """
    try:
        command = [
            'ffmpeg', '-y',
            '-i', ogg_path,
            '-ar', '16000',
            '-ac', '1',
            wav_path
        ]
        # Используем subprocess.run для синхронного вызова (будет обернуто в thread в сервисе если надо)
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"Successfully converted {ogg_path} to {wav_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg conversion failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error during audio conversion: {e}")
        return False

def cleanup_files(*file_paths: str):
    """Удаляет указанные файлы."""
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
                logger.info(f"Removed temporary file: {path}")
            except Exception as e:
                logger.warning(f"Failed to remove file {path}: {e}")

def get_file_base64(file_path: str) -> Optional[str]:
    """Кодирует содержимое файла в base64."""
    try:
        import base64
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Error encoding file to base64: {e}")
        return None
