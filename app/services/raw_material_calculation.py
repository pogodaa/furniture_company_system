"""
Расчет необходимого сырья для производства продукции
"""
from math import ceil
from typing import Tuple, Optional
from sqlalchemy.orm import Session

def calculate_raw_material(
    db: Session,
    product_type_id: int,
    material_type_id: int,
    product_quantity: int,
    param1: float,
    param2: float
) -> int:
    """
    Рассчитать количество сырья для производства
    
    Args:
        db: Сессия БД
        product_type_id: ID типа продукции
        material_type_id: ID типа материала
        product_quantity: Количество продукции (целое > 0)
        param1: Первый параметр продукции (вещественное > 0)
        param2: Второй параметр продукции (вещественное > 0)
        
    Returns:
        int: Количество сырья (целое число) или -1 при ошибке
    """
    from app.database.database import ProductType, MaterialType
    
    # 1. Проверяем существование типа продукции
    product_type = db.query(ProductType).filter(ProductType.id == product_type_id).first()
    if not product_type:
        return -1
    
    # 2. Проверяем существование типа материала
    material_type = db.query(MaterialType).filter(MaterialType.id == material_type_id).first()
    if not material_type:
        return -1
    
    # 3. Проверяем корректность входных данных
    if product_quantity <= 0 or param1 <= 0 or param2 <= 0:
        return -1
    
    try:
        # 4. Расчет по формуле из ТЗ
        # Произведение параметров продукции
        params_product = param1 * param2
        
        # Умножаем на коэффициент типа продукции
        material_per_unit = params_product * product_type.coefficient
        
        # Общее количество без учета потерь
        total_without_loss = material_per_unit * product_quantity
        
        # Учет потерь сырья (процент хранится как 0.8 для 0.8%)
        # Преобразуем процент в коэффициент: 0.8% -> 0.008
        loss_factor = 1 + (material_type.loss_percentage / 100)
        
        # Количество с учетом потерь
        total_with_loss = total_without_loss * loss_factor
        
        # Округляем ВВЕРХ до целого числа (ceil)
        total_rounded = ceil(total_with_loss)
        
        return total_rounded
        
    except (ValueError, TypeError, ZeroDivisionError) as e:
        # Логирование ошибки при необходимости
        print(f"Ошибка расчета сырья: {e}")
        return -1

def calculate_raw_material_with_details(
    db: Session,
    product_type_id: int,
    material_type_id: int,
    product_quantity: int,
    param1: float,
    param2: float
) -> Tuple[Optional[int], Optional[dict]]:
    """
    Рассчитать сырье с возвратом деталей расчета
    
    Returns:
        Tuple[result, details] где result - количество сырья или -1,
        details - словарь с деталями расчета или None
    """
    from app.database.database import ProductType, MaterialType
    
    # Получаем данные
    product_type = db.query(ProductType).filter(ProductType.id == product_type_id).first()
    material_type = db.query(MaterialType).filter(MaterialType.id == material_type_id).first()
    
    if not product_type or not material_type:
        return -1, None
    
    if product_quantity <= 0 or param1 <= 0 or param2 <= 0:
        return -1, None
    
    try:
        # Расчет
        params_product = param1 * param2
        material_per_unit = params_product * product_type.coefficient
        total_without_loss = material_per_unit * product_quantity
        loss_factor = 1 + (material_type.loss_percentage / 100) 
        total_with_loss = total_without_loss * loss_factor
        total_rounded = ceil(total_with_loss)
        
        # Формируем детали
        details = {
            "product_type_name": product_type.name,
            "material_name": material_type.name,
            "coefficient": product_type.coefficient,
            "loss_percentage": material_type.loss_percentage,
            "product_quantity": product_quantity,
            "param1": param1,
            "param2": param2,
            "params_product": params_product,
            "material_per_unit": round(material_per_unit, 4),
            "total_without_loss": round(total_without_loss, 4),
            "loss_factor": round(loss_factor, 6),
            "total_with_loss": round(total_with_loss, 4),
            "total_rounded": total_rounded
        }
        
        return total_rounded, details
        
    except Exception as e:
        print(f"Ошибка расчета: {e}")
        return -1, None