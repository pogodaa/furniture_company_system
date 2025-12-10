from fastapi import APIRouter
from app.api.endpoints import products, workshops, catalog

# Создаем главный роутер
router = APIRouter()

router.include_router(products.router, tags=["Products"])
router.include_router(workshops.router, tags=["Workshops"])
router.include_router(catalog.router, tags=["Catalog"])


