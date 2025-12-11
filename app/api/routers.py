from fastapi import APIRouter
from app.api.endpoints import products, workshops, catalog, calculations, production

# Создаем главный роутер
router = APIRouter()

router.include_router(products.router, tags=["Products"])
router.include_router(workshops.router, tags=["Workshops"])
router.include_router(production.router, tags=["Production"])
router.include_router(calculations.router, tags=["Calculations"])
router.include_router(catalog.router, tags=["Catalog"])