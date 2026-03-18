import logging
import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from adapters.max_adapter import router as max_router
from adapters.telegram_adapter import router as telegram_router

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Omnichannel AI Core",
    description="FastAPI + GigaAM Omnichannel Platform"
)

# Подключение роутеров
app.include_router(max_router)
app.include_router(telegram_router)

@app.on_event("startup")
async def startup_event():
    """Предзагрузка тяжелых моделей при старте сервера."""
    from services.audio_service import get_gigaam_pipeline
    logger.info("Universal Bot Core is starting up...")
    # Запускаем загрузку модели ASR в фоновом режиме (через asyncio.to_thread или просто вызвав)
    # Поскольку get_gigaam_pipeline закеширован lru_cache, первый вызов загрузит модель
    try:
        import asyncio
        await asyncio.to_thread(get_gigaam_pipeline)
        logger.info("GigaAM v3 STT model pre-loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to pre-load GigaAM model: {e}")

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Omnichannel AI Core is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=False
    )
