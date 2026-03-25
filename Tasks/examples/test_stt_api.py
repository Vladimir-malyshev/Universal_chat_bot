import asyncio
import httpx
import sys
import os

# Используем тестовый аудио-файл из репозитория STT (если есть) или любой другой
TEST_AUDIO_PATH = r"D:\VSCODE\Projects\speech-service\audio_2025-07-31_02-33-31.ogg"
BASE_URL = "http://82.202.141.104:8000"

async def test_transcription():
    if not os.path.exists(TEST_AUDIO_PATH):
        print(f"File not found: {TEST_AUDIO_PATH}")
        return

    print(f"[1] Uploading file {TEST_AUDIO_PATH} to {BASE_URL}/transcribe")
    
    # Шаг 1: Загрузка
    async with httpx.AsyncClient(timeout=30.0) as client:
        with open(TEST_AUDIO_PATH, "rb") as f:
            files = {"file": ("test_audio.ogg", f, "audio/ogg")}
            response = await client.post(f"{BASE_URL}/transcribe", files=files)
            
        if response.status_code not in (200, 202):
            print(f"Failed to upload: {response.status_code} - {response.text}")
            return
            
        data = response.json()
        job_id = data.get("job_id")
        position = data.get("position")
        print(f"Upload successful. Job ID: {job_id}, Queue position: {position}")

        # Шаг 2: Поллинг
        print("[2] Polling for results...")
        while True:
            await asyncio.sleep(2.0)  # Ждем 2 секунды между запросами
            
            status_resp = await client.get(f"{BASE_URL}/status/{job_id}")
            
            if status_resp.status_code == 404:
                print("Error: Task suddenly disappeared (404 Not Found)")
                break
                
            status_data = status_resp.json()
            status = status_data.get("status")
            
            if status == "queued":
                print(f"Status: queued (size: {status_data.get('queue_size')})")
            elif status == "processing":
                print(f"Status: processing...")
            elif status == "done":
                print(f"\n[DONE] Transcription Result:\n---")
                print(status_data.get("text"))
                print("---")
                break
            elif status == "error":
                print(f"\n[ERROR] Transcription Failed: {status_data.get('error')}")
                break
            else:
                print(f"Unknown status: {status_data}")

if __name__ == "__main__":
    asyncio.run(test_transcription())
