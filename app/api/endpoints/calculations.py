"""
Эндпоинты для расчетов
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database.session import get_db
from app.database.database import Product, ProductType, MaterialType, Workshop, product_workshop_table
from app.services.production_time import calculate_total_production_time
from app.services.raw_material_calculation import (
    calculate_raw_material,
    calculate_raw_material_with_details
)
from app.schemas.calculation import (
    RawMaterialRequest,
    RawMaterialResponse,
    ProductionDetailsRequest
)

router = APIRouter(prefix="/calculations", tags=["Calculations"])

@router.get("/production-details/{product_id}")
def get_production_details(
    product_id: int,
    db: Session = Depends(get_db)
):
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
            Workshop.workshop_type,
            Workshop.employee_count,
            product_workshop_table.c.manufacturing_time_hours
        )
        .select_from(product_workshop_table)
        .join(Workshop, Workshop.id == product_workshop_table.c.workshop_id)
        .where(product_workshop_table.c.product_id == product_id)
    ).fetchall()
    
    # 3. Рассчитываем общее время
    total_time = calculate_total_production_time(db, product_id)
    
    # 4. Формируем детали цехов (для Задания 4)
    workshops_detailed = []
    for name, w_type, emp_count, time in workshop_times:
        workshops_detailed.append({
            "workshop_name": name,
            "workshop_type": w_type,
            "employee_count": emp_count,
            "time_hours": float(time),
            "description": f"Изготовление в цехе '{name}' ({w_type}, {emp_count} чел.)"
        })
    
    return {
        "product": {
            "id": product.id,
            "name": product.name,
            "article": product.article,
            "product_type": product.product_type.name,
            "main_material": product.material.name,
            "min_partner_price": product.min_partner_price
        },
        "production_steps": workshops_detailed,
        "summary": {
            "total_production_time": total_time,
            "workshops_count": len(workshop_times),
            "average_time_per_workshop": round(
                total_time / len(workshop_times) if workshop_times else 0, 
                2
            ),
            "total_employees": sum(w[2] for w in workshop_times) if workshop_times else 0
        },
        "calculation_notes": "Время изготовления складывается из времени нахождения в каждом цехе"
    }

@router.post(
    "/raw-material",
    response_model=RawMaterialResponse,
    summary="Рассчитать необходимое количество сырья"
)
def calculate_raw_material_endpoint(
    request: RawMaterialRequest,
    db: Session = Depends(get_db)
):
    """
    Расчет количества сырья для производства продукции
    
    Формула:
    Количество_сырья = ceil(
        (кол-во_продукции × параметр1 × параметр2 × коэффициент_типа) 
        × (1 + процент_потерь / 100)
    )
    
    Пример:
    - Тип: Гостиные (коэффициент 3.5)
    - Материал: Мебельный щит (потери 0.8%)
    - Количество: 10 штук
    - Параметр1: 2.5 м Длина
    - Параметр2: 1.8 м Ширина
    
    Расчет:
    1. 10 × 2.5 × 1.8 × 3.5 = 157.5
    2. 157.5 × (1 + 0.8/100) = 157.5 × 1.008 = 158.76
    3. ceil(158.76) = 159 единиц сырья
    """
    # Используем функцию с деталями
    result, details = calculate_raw_material_with_details(
        db=db,
        product_type_id=request.product_type_id,
        material_type_id=request.material_type_id,
        product_quantity=request.product_quantity,
        param1=request.param1,
        param2=request.param2
    )
    
    if result == -1 or details is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Некорректные данные. Проверьте: "
                "1) Существование типа продукции и материала, "
                "2) Положительные значения количества и параметров"
            )
        )
    
    return RawMaterialResponse(
        raw_material_quantity=result,
        product_type_id=request.product_type_id,
        material_type_id=request.material_type_id,
        product_quantity=request.product_quantity,
        param1=request.param1,
        param2=request.param2,
        calculation_details=details
    )

@router.get("/product/{product_id}/workshops-detailed")
def get_product_workshops_detailed(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить детальный список цехов для продукта
    с временем изготовления и количеством людей
    
    Для интеграции в интерфейс (Задание 4)
    """
    from app.database.database import product_workshop_table
    
    # 1. Проверяем продукт
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # 2. Получаем цеха с деталями
    workshops_detailed = db.execute(
        select(
            Workshop.id,
            Workshop.name,
            Workshop.workshop_type,
            Workshop.employee_count,
            product_workshop_table.c.manufacturing_time_hours
        )
        .select_from(product_workshop_table)
        .join(Workshop, Workshop.id == product_workshop_table.c.workshop_id)
        .where(product_workshop_table.c.product_id == product_id)
    ).fetchall()
    
    # 3. Форматируем ответ
    workshops_list = []
    for w_id, name, w_type, emp_count, time in workshops_detailed:
        workshops_list.append({
            "workshop_id": w_id,
            "workshop_name": name,
            "workshop_type": w_type,
            "employee_count": emp_count,
            "manufacturing_time_hours": float(time) if time else 0.0
        })
    
    # 4. Общее время
    total_time = calculate_total_production_time(db, product_id)
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "product_article": product.article,
        "workshops": workshops_list,
        "summary": {
            "total_workshops": len(workshops_list),
            "total_production_time": total_time,
            "total_employees_involved": sum(w["employee_count"] for w in workshops_list)
        }
    }