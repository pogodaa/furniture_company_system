"""
Схемы для типов материалов
"""
from pydantic import BaseModel

class MaterialTypeBase(BaseModel):
    name: str
    loss_percentage: float

class MaterialTypeCreate(MaterialTypeBase):
    pass

class MaterialTypeResponse(MaterialTypeBase):
    id: int
    
    class Config:
        from_attributes = True