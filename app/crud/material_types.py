"""
CRUD для типов материалов
"""
from sqlalchemy.orm import Session
from app.database.database import MaterialType

class MaterialTypeCRUD:
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        """Получить все типы материалов"""
        return db.query(MaterialType).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, material_id: int):
        """Получить тип материала по ID"""
        return db.query(MaterialType).filter(MaterialType.id == material_id).first()
    
    @staticmethod
    def get_material_products(db: Session, material_id: int):
        """Получить продукты из этого материала"""
        material = db.query(MaterialType).filter(MaterialType.id == material_id).first()
        if material:
            return material.products
        return []

material_type_crud = MaterialTypeCRUD()