from pydantic import BaseModel, Field

class ProductBase(BaseModel):
    """Базовые поля продукта"""
    article: str
    name: str
    product_type_id: int
    material_id: int
    min_partner_price: float

class ProductCreate(ProductBase):
    """Для создания продукта"""
    pass

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