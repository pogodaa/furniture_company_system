"""
Расчет времени изготовления продукции
Просто суммируем время по всем цехам
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.database.database import product_workshop_table

def calculate_total_production_time(db: Session, product_id: int) -> int:
    """
    Рассчитать общее время изготовления продукта
    Сумма времени по всем цехам
    """
    # Правильный способ с SQLAlchemy 2.0
    stmt = select(func.sum(product_workshop_table.c.manufacturing_time_hours))\
        .where(product_workshop_table.c.product_id == product_id)
    
    result = db.execute(stmt).scalar()
    
    return float(result) if result else 0.0