from pydantic import BaseModel, Field, validator
from decimal import Decimal
from typing import Optional

class ProductBase(BaseModel):
    """Базовые поля продукта"""
    article: str = Field(..., min_length=1, max_length=50, description="Артикул продукта")
    name: str = Field(..., min_length=1, max_length=200, description="Наименование продукта")
    product_type_id: int = Field(..., gt=0, description="ID типа продукции")
    material_id: int = Field(..., gt=0, description="ID материала")
    min_partner_price: float = Field(..., gt=0, description="Минимальная стоимость для партнера")

    @validator('min_partner_price')
    def validate_price(cls, v):
        """Валидация стоимости - не может быть отрицательной"""
        if v < 0:
            raise ValueError('Стоимость не может быть отрицательной')
        return round(v, 2)  # Округляем до сотых

class ProductCreate(ProductBase):
    """Для создания продукта"""
    pass

class ProductUpdate(BaseModel):
    """Для обновления продукта (все поля опциональны)"""
    article: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    product_type_id: Optional[int] = Field(None, gt=0)
    material_id: Optional[int] = Field(None, gt=0)
    min_partner_price: Optional[float] = Field(None, gt=0)
    
    @validator('min_partner_price')
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Стоимость не может быть отрицательной')
        return round(v, 2) if v is not None else None

class ProductResponse(BaseModel):
    """
    Ответ API для макета:
    Тип | Наименование продукта | Время изготовления
    Артикул
    Минимальная стоимость для партнера  
    Основной материал
    """
    # Первая строка макета
    product_type: str  # "Гостиные", "Прихожие" и т.д.
    product_name: str  # "Комплект мебели для гостиной Ольха горная"
    production_time: int = Field(ge=0) # целое число >= 0
    
    # Остальные строки макета
    article: str
    min_partner_price: float
    main_material: str  # "Мебельный щит из массива дерева"
    
    # Дополнительно (не в макете, но полезно)
    id: int
    
    class Config:
        from_attributes = True  # Позволяет создать из SQLAlchemy объекта