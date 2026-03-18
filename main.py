import logging
from fastapi import FastAPI
from adapters.max_adapter import router as max_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Omnichannel AI Core",
    description="FastAPI + GigaAM Omnichannel Platform"
)

# Подключение роутера MAX
app.include_router(max_router)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Omnichannel AI Core is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
