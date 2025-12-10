"""
Эндпоинты для справочников (типы продукции, материалы)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.crud.product_types import product_type_crud
from app.crud.material_types import material_type_crud
from app.schemas.product_type import ProductTypeResponse
from app.schemas.material_type import MaterialTypeResponse

router = APIRouter(prefix="/catalog", tags=["Catalog"])

# Типы продукции
@router.get("/product-types", response_model=List[ProductTypeResponse])
def get_product_types(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получить список типов продукции
    """
    return product_type_crud.get_all(db, skip, limit)

@router.get("/product-types/{type_id}", response_model=ProductTypeResponse)
def get_product_type(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить тип продукции по ID
    """
    product_type = product_type_crud.get_by_id(db, type_id)
    if not product_type:
        raise HTTPException(status_code=404, detail="Тип продукции не найден")
    return product_type

# Типы материалов  
@router.get("/material-types", response_model=List[MaterialTypeResponse])
def get_material_types(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получить список типов материалов
    """
    return material_type_crud.get_all(db, skip, limit)

@router.get("/material-types/{material_id}", response_model=MaterialTypeResponse)
def get_material_type(
    material_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить тип материала по ID
    """
    material = material_type_crud.get_by_id(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Тип материала не найден")
    return material