from fastapi import FastAPI
from app.api.config_fastapi import config
from app.api.routers import router

# Создаем приложение
app = FastAPI(
    title=config.title,
    version=config.version,
    debug=config.debug,
    docs_url=config.docs_url,
    redoc_url=config.redoc_url,
)

# Подключаем роутеры
app.include_router(router)

# Простой тестовый эндпоинт
@app.get("/")
def read_root():
    return {
        "message": "Добро пожаловать в систему учета мебельной компании",
        "docs": "/docs",
        "api": "/api/v1"
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "furniture-api"}

# Запуск для разработки
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=config.reload
    ) 