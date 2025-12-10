"""
CRUD для типов продукции
"""
from sqlalchemy.orm import Session
from app.database.database import ProductType

class ProductTypeCRUD:
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        """Получить все типы продукции"""
        return db.query(ProductType).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, type_id: int):
        """Получить тип по ID"""
        return db.query(ProductType).filter(ProductType.id == type_id).first()
    
    @staticmethod
    def get_type_products(db: Session, type_id: int):
        """Получить продукты этого типа"""
        product_type = db.query(ProductType).filter(ProductType.id == type_id).first()
        if product_type:
            return product_type.products
        return []

product_type_crud = ProductTypeCRUD()