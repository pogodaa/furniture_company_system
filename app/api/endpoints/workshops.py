"""
Эндпоинты для цехов
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.crud.workshops import workshop_crud
from app.schemas.workshop import (
    WorkshopResponse, WorkshopCreate, WorkshopUpdate, WorkshopProductResponse
)

# Создаем роутер
router = APIRouter(prefix="/workshops", tags=["Workshops"])

@router.get("/", response_model=List[WorkshopResponse])
def get_workshops(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получить список цехов
    """
    workshops = workshop_crud.get_all(db, skip, limit)
    return workshops

@router.get("/{workshop_id}", response_model=WorkshopResponse)
def get_workshop(
    workshop_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить цех по ID
    """
    workshop = workshop_crud.get_by_id(db, workshop_id)
    if not workshop:
        raise HTTPException(status_code=404, detail="Цех не найден")
    return workshop

@router.post("/", response_model=WorkshopResponse, status_code=status.HTTP_201_CREATED)
def create_workshop(
    workshop_data: WorkshopCreate,
    db: Session = Depends(get_db)
):
    """
    Создать новый цех
    
    - **name**: Название цеха
    - **workshop_type**: Тип цеха
    - **employee_count**: Количество человек для производства
    """
    workshop = workshop_crud.create(db, workshop_data)
    return workshop

@router.put("/{workshop_id}", response_model=WorkshopResponse)
def update_workshop(
    workshop_id: int,
    workshop_data: WorkshopUpdate,
    db: Session = Depends(get_db)
):
    """
    Обновить цех по ID
    
    Все поля опциональны. Обновляются только переданные поля.
    """
    workshop = workshop_crud.update(db, workshop_id, workshop_data)
    if not workshop:
        raise HTTPException(status_code=404, detail="Цех не найден")
    return workshop

@router.delete("/{workshop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workshop(
    workshop_id: int,
    db: Session = Depends(get_db)
):
    """
    Удалить цех по ID
    
    Внимание: Нельзя удалить цех, если с ним связаны продукты!
    """
    success = workshop_crud.delete(db, workshop_id)
    if not success:
        raise HTTPException(status_code=404, detail="Цех не найден")
    return None

@router.get("/{workshop_id}/products")
def get_workshop_products(
    workshop_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить продукты для цеха
    """
    from app.database.database import Product, ProductType, MaterialType
    from app.services.production_time import calculate_total_production_time
    
    # 1. Получаем цех
    workshop = workshop_crud.get_by_id(db, workshop_id)
    if not workshop:
        raise HTTPException(status_code=404, detail="Цех не найден")
    
    # 2. Обрабатываем каждый продукт
    products_response = []
    
    for product in workshop.products:
        try:
            # Получаем связанные данные (тип и материал)
            product_with_details = db.query(Product)\
                .join(ProductType, Product.product_type_id == ProductType.id)\
                .join(MaterialType, Product.material_id == MaterialType.id)\
                .filter(Product.id == product.id)\
                .first()
            
            if product_with_details:
                # Создаем ответ по новой схеме
                product_response = WorkshopProductResponse(
                    id=product.id,
                    name=product.name,
                    article=product.article,
                    min_partner_price=product.min_partner_price,
                    product_type_name=product_with_details.product_type.name,
                    material_name=product_with_details.material.name
                )
                products_response.append(product_response)
                
        except Exception as e:
            # Пропускаем продукты с ошибками
            print(f"Ошибка обработки продукта {product.id} в цехе {workshop_id}: {e}")
            continue
    
    # 3. Возвращаем структурированный ответ
    return {
        "workshop_id": workshop_id,
        "workshop_name": workshop.name,
        "products": products_response
    }