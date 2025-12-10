from pydantic import BaseModel

class FastAPIConfig(BaseModel):
    title: str = "Мебельная компания - Система учета"
    version: str = "1.0.0"
    debug: bool = True
    
    # Документация
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    
    # Для разработки
    reload: bool = True

config = FastAPIConfig()