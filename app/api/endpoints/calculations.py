"""
Эндпоинты для расчетов (вкладка "Расчёт времени")
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.session import get_db
from app.database.database import Product, ProductType, MaterialType, Workshop, product_workshop_table
from app.services.production_time import calculate_total_production_time

router = APIRouter(prefix="/calculations", tags=["Calculations"])

@router.get("/production-details/{product_id}")
def get_production_details(product_id: int, db: Session = Depends(get_db)):
    """
    Детальный расчет времени изготовления продукта
    """
    # 1. Получаем продукт с названиями
    product = db.query(Product)\
        .join(ProductType, Product.product_type_id == ProductType.id)\
        .join(MaterialType, Product.material_id == MaterialType.id)\
        .filter(Product.id == product_id)\
        .first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # 2. Получаем цеха и время
    workshop_times = db.execute(
        select(
            Workshop.name,
            product_workshop_table.c.manufacturing_time_hours
        )
        .select_from(product_workshop_table)
        .join(Workshop, Workshop.id == product_workshop_table.c.workshop_id)
        .where(product_workshop_table.c.product_id == product_id)
    ).fetchall()
    
    # 3. Рассчитываем общее время
    total_time = calculate_total_production_time(db, product_id)
    
    return {
        "product": {
            "id": product.id,
            "name": product.name,
            "article": product.article,
            "product_type": product.product_type.name,
            "main_material": product.material.name
        },
        "production_steps": [
            {
                "workshop_name": name,
                "time_hours": float(time),
                "description": f"Изготовление в цехе '{name}'"
            }
            for name, time in workshop_times
        ],
        "summary": {
            "total_production_time": total_time,
            "workshops_count": len(workshop_times),
            "average_time_per_workshop": total_time / len(workshop_times) if workshop_times else 0
        },
        "calculation_notes": "Время изготовления складывается из времени нахождения в каждом цехе"
    }