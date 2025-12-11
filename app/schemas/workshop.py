from pydantic import BaseModel, Field, validator
from typing import Optional, List

class WorkshopBase(BaseModel):
    """Базовые поля цеха"""
    name: str = Field(..., min_length=1, max_length=100, description="Название цеха")
    workshop_type: str = Field(..., min_length=1, max_length=50, description="Тип цеха")
    employee_count: int = Field(..., gt=0, description="Количество человек для производства")

class WorkshopCreate(WorkshopBase):
    """Для создания цеха"""
    pass

class WorkshopUpdate(BaseModel):
    """Для обновления цеха (все поля опциональны)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    workshop_type: Optional[str] = Field(None, min_length=1, max_length=50)
    employee_count: Optional[int] = Field(None, gt=0)

class WorkshopResponse(WorkshopBase):
    """Ответ API для цеха"""
    id: int
    
    class Config:
        from_attributes = True

class WorkshopProductResponse(BaseModel):
    """Продукт в контексте цеха"""
    id: int
    name: str
    article: str
    min_partner_price: float
    product_type_name: str
    material_name: str
    
    class Config:
        from_attributes = True