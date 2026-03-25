import asyncio
import logging
import os
import httpx

logger = logging.getLogger(__name__)

async def transcribe_audio_async(file_path: str) -> str:
    """Асинхронная загрузка файла на внешний STT сервис и ожидание результата."""
    base_url = os.getenv("STT_SERVICE_URL", "http://82.202.141.104:8000")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return ""
        
    logger.info(f"Uploading {file_path} to STT service at {base_url}/transcribe")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(file_path, "rb") as f:
                # Отправляем файл на сервер
                files = {"file": (os.path.basename(file_path), f, "audio/wav")}
                response = await client.post(f"{base_url}/transcribe", files=files)
                
            if response.status_code not in (200, 202):
                logger.error(f"STT Upload Failed: {response.status_code} - {response.text}")
                return ""
                
            data = response.json()
            job_id = data.get("job_id")
            
            if not job_id:
                logger.error("No job_id received from STT service.")
                return ""
                
            logger.info(f"Upload successful. Polling job ID: {job_id}")
            
            # Поллинг статуса
            max_attempts = 120  # ~4 минуты
            for _ in range(max_attempts):
                await asyncio.sleep(2.0)
                
                status_resp = await client.get(f"{base_url}/status/{job_id}")
                
                if status_resp.status_code == 404:
                    logger.error(f"Task {job_id} not found on STT server.")
                    break
                    
                status_data = status_resp.json()
                status = status_data.get("status")
                
                if status == "done":
                    logger.info(f"Transcription for {job_id} completed successfully.")
                    return status_data.get("text", "")
                elif status == "error":
                    logger.error(f"Transcription error for {job_id}: {status_data.get('error')}")
                    return ""
                elif status in ["queued", "processing"]:
                    # Продолжаем ждать
                    continue
                else:
                    logger.warning(f"Unknown STT task status: {status_data}")
                    
            logger.error(f"Timeout waiting for STT transcription for job {job_id}")
            return ""
            
    except Exception as e:
        logger.exception(f"Exception during external STT processing: {e}")
        return ""
