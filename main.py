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

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """События жизненного цикла FastAPI."""
    logger.info("Universal Bot Core is starting up...")
    # Здесь можно добавить инициализацию пулов БД или других легковесных сервисов
    yield
    logger.info("Universal Bot Core is shutting down...")

app = FastAPI(
    title="Omnichannel AI Core",
    description="FastAPI + GigaAM Omnichannel Platform",
    lifespan=lifespan
)

# Подключение роутеров
app.include_router(max_router)
app.include_router(telegram_router)

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
