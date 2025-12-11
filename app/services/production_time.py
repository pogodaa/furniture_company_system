"""
Расчет времени изготовления продукции
Суммируем время по всем цехам и округляем до целого
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.database.database import product_workshop_table

def calculate_total_production_time(db: Session, product_id: int) -> int:
    """
    Рассчитать общее время изготовления продукта
    Возвращает целое неотрицательное число (часы)
    """
    # Суммируем время по всем цехам
    stmt = select(func.sum(product_workshop_table.c.manufacturing_time_hours))\
        .where(product_workshop_table.c.product_id == product_id)
    
    result = db.execute(stmt).scalar()
    
    # Если нет результата или None -> 0
    if result is None:
        return 0
    
    # Округляем до ближайшего целого
    # 3.5 -> 4, 3.4 -> 3, 5.0 -> 5
    return int(round(float(result)))