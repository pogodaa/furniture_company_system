"""
Эндпоинты для связи продукт-цех (производство)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.database.database import Product, Workshop, product_workshop_table
from app.schemas.product import ProductResponse
from app.services.production_time import calculate_total_production_time

router = APIRouter(prefix="/production", tags=["Production"])

@router.post("/product/{product_id}/workshop/{workshop_id}")
def add_product_to_workshop(
    product_id: int,
    workshop_id: int,
    manufacturing_time_hours: float,
    db: Session = Depends(get_db)
):
    """
    Добавить продукт в цех с указанием времени изготовления
    
    - **manufacturing_time_hours**: Время изготовления в цехе (часы)
    """
    # Проверяем существование продукта
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Проверяем существование цеха
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Цех не найден")
    
    # Проверяем, не существует ли уже связь
    existing_link = db.execute(
        product_workshop_table.select().where(
            (product_workshop_table.c.product_id == product_id) &
            (product_workshop_table.c.workshop_id == workshop_id)
        )
    ).first()
    
    if existing_link:
        raise HTTPException(status_code=400, detail="Продукт уже связан с этим цехом")
    
    # Проверяем время (не может быть отрицательным)
    if manufacturing_time_hours < 0:
        raise HTTPException(status_code=400, detail="Время изготовления не может быть отрицательным")
    
    # Создаем связь
    try:
        stmt = product_workshop_table.insert().values(
            product_id=product_id,
            workshop_id=workshop_id,
            manufacturing_time_hours=manufacturing_time_hours
        )
        db.execute(stmt)
        db.commit()
        
        return {
            "message": "Продукт успешно добавлен в цех",
            "product_id": product_id,
            "workshop_id": workshop_id,
            "manufacturing_time_hours": manufacturing_time_hours
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании связи: {str(e)}")

@router.delete("/product/{product_id}/workshop/{workshop_id}")
def remove_product_from_workshop(
    product_id: int,
    workshop_id: int,
    db: Session = Depends(get_db)
):
    """
    Удалить продукт из цеха
    """
    # Удаляем связь
    try:
        stmt = product_workshop_table.delete().where(
            (product_workshop_table.c.product_id == product_id) &
            (product_workshop_table.c.workshop_id == workshop_id)
        )
        result = db.execute(stmt)
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Связь продукт-цех не найдена")
        
        return {
            "message": "Продукт успешно удален из цеха",
            "product_id": product_id,
            "workshop_id": workshop_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении связи: {str(e)}")

@router.get("/product/{product_id}/workshops")
def get_product_workshops(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить список цехов для продукта с временем изготовления
    """
    # Проверяем существование продукта
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Получаем цеха с временем изготовления
    workshops_with_time = []
    
    for workshop in product.workshops:
        # Получаем время изготовления для этого цеха
        result = db.execute(
            product_workshop_table.select().where(
                (product_workshop_table.c.product_id == product_id) &
                (product_workshop_table.c.workshop_id == workshop.id)
            )
        ).first()
        
        if result:
            workshops_with_time.append({
                "workshop_id": workshop.id,
                "workshop_name": workshop.name,
                "workshop_type": workshop.workshop_type,
                "employee_count": workshop.employee_count,
                "manufacturing_time_hours": result.manufacturing_time_hours
            })
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "workshops": workshops_with_time,
        "total_production_time": calculate_total_production_time(db, product_id)
    }