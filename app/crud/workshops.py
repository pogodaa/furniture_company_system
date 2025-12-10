"""
Простые CRUD операции для цехов
"""
from sqlalchemy.orm import Session
from app.database.database import Workshop
from app.schemas.workshop import WorkshopCreate

class WorkshopCRUD:
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        """Получить все цехи"""
        return db.query(Workshop).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, workshop_id: int):
        """Получить цех по ID"""
        return db.query(Workshop).filter(Workshop.id == workshop_id).first()
    
    @staticmethod
    def get_workshop_products(db: Session, workshop_id: int):
        """Получить продукты для цеха"""
        workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
        if workshop:
            return workshop.products
        return []
    
    @staticmethod
    def create(db: Session, workshop_data: WorkshopCreate):
        """Создать новый цех"""
        workshop = Workshop(**workshop_data.dict())
        db.add(workshop)
        db.commit()
        db.refresh(workshop)
        return workshop

# Создаем экземпляр
workshop_crud = WorkshopCRUD()