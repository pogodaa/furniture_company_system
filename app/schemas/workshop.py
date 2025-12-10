"""
Схемы для цехов
"""
from pydantic import BaseModel
from typing import List, Optional

class WorkshopBase(BaseModel):
    name: str
    workshop_type: str
    employee_count: int

class WorkshopCreate(WorkshopBase):
    pass

class WorkshopUpdate(BaseModel):
    name: str | None = None
    workshop_type: str | None = None
    employee_count: int | None = None

class WorkshopResponse(WorkshopBase):
    id: int
    
    class Config:
        from_attributes = True


class WorkshopProductResponse(BaseModel):
    """Схема для отображения продуктов цеха"""
    id: int
    name: str
    article: str
    min_partner_price: float
    product_type_name: Optional[str] = None  # Название типа вместо ID
    material_name: Optional[str] = None      # Название материала вместо ID
    
    class Config:
        from_attributes = True

class WorkshopProductsResponse(BaseModel):
    """Полный ответ с продуктами цеха"""
    workshop_id: int
    workshop_name: str
    products: List[WorkshopProductResponse]