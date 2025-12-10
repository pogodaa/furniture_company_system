"""
Схемы для типов продукции
"""
from pydantic import BaseModel

class ProductTypeBase(BaseModel):
    name: str
    coefficient: float

class ProductTypeCreate(ProductTypeBase):
    pass

class ProductTypeResponse(ProductTypeBase):
    id: int
    
    class Config:
        from_attributes = True