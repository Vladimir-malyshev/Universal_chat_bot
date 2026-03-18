import logging
import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from adapters.max_adapter import router as max_router
from adapters.telegram_adapter import router as telegram_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
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

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Omnichannel AI Core is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
