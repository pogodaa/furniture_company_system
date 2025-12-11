from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.database.database import Workshop
from app.schemas.workshop import WorkshopCreate, WorkshopUpdate

class WorkshopCRUD:
    """CRUD операции для цехов"""
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        """Получить все цехи"""
        return db.query(Workshop).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, workshop_id: int):
        """Получить цех по ID"""
        return db.query(Workshop).filter(Workshop.id == workshop_id).first()
    
    @staticmethod
    def create(db: Session, workshop_data: WorkshopCreate):
        """Создать новый цех"""
        # Проверяем уникальность названия
        existing_workshop = db.query(Workshop).filter(Workshop.name == workshop_data.name).first()
        if existing_workshop:
            raise HTTPException(status_code=400, detail="Цех с таким названием уже существует")
        
        try:
            workshop = Workshop(**workshop_data.dict())
            db.add(workshop)
            db.commit()
            db.refresh(workshop)
            return workshop
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Ошибка целостности данных: {str(e)}")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при создании цеха: {str(e)}")
    
    @staticmethod
    def update(db: Session, workshop_id: int, workshop_data: WorkshopUpdate):
        """Обновить цех"""
        workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
        if not workshop:
            return None
        
        update_data = workshop_data.dict(exclude_unset=True)
        
        # Проверяем уникальность названия, если оно обновляется
        if 'name' in update_data and update_data['name'] != workshop.name:
            existing_workshop = db.query(Workshop).filter(Workshop.name == update_data['name']).first()
            if existing_workshop:
                raise HTTPException(status_code=400, detail="Цех с таким названием уже существует")
        
        try:
            for field, value in update_data.items():
                if value is not None:
                    setattr(workshop, field, value)
            
            db.commit()
            db.refresh(workshop)
            return workshop
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при обновлении цеха: {str(e)}")
    
    @staticmethod
    def delete(db: Session, workshop_id: int):
        """Удалить цех"""
        workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
        if not workshop:
            return False
        
        # Проверяем, нет ли связанных продуктов
        if workshop.products:
            raise HTTPException(
                status_code=400, 
                detail="Нельзя удалить цех, так как с ним связаны продукты. "
                       "Сначала удалите связи с продуктами."
            )
        
        try:
            db.delete(workshop)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при удалении цеха: {str(e)}")

# Создаем экземпляр для использования
workshop_crud = WorkshopCRUD()