"""
Pydantic схемы для расчетов
"""
from pydantic import BaseModel, Field, validator
from typing import Optional

class RawMaterialRequest(BaseModel):
    """Запрос на расчет сырья"""
    product_type_id: int = Field(..., gt=0, description="ID типа продукции")
    material_type_id: int = Field(..., gt=0, description="ID типа материала")
    product_quantity: int = Field(..., gt=0, description="Количество продукции (штук)")
    param1: float = Field(..., gt=0, description="Первый параметр продукции (м)")
    param2: float = Field(..., gt=0, description="Второй параметр продукции (м)")
    
    @validator('param1', 'param2')
    def validate_positive(cls, v):
        """Проверка что параметры положительные"""
        if v <= 0:
            raise ValueError('Параметры должны быть положительными числами')
        return round(v, 4)  # Округляем до 4 знаков

class RawMaterialResponse(BaseModel):
    """Ответ расчета сырья"""
    raw_material_quantity: int = Field(..., ge=0, description="Количество сырья (целое)")
    product_type_id: int
    material_type_id: int
    product_quantity: int
    param1: float
    param2: float
    calculation_details: dict = Field(..., description="Детали расчета")
    
    class Config:
        from_attributes = True

class ProductionDetailsRequest(BaseModel):
    """Запрос деталей производства продукта"""
    product_id: int = Field(..., gt=0, description="ID продукта")

class WorkshopProductionRequest(BaseModel):
    """Запрос деталей производства цеха"""
    workshop_id: int = Field(..., gt=0, description="ID цеха")