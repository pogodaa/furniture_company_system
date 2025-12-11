from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.database.database import Product, ProductType, MaterialType
from app.schemas.product import ProductCreate, ProductUpdate

class ProductCRUD:
    """CRUD операции для продукции"""
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        """Получить все продукты"""
        return db.query(Product).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_with_details(db: Session, product_id: int):
        """Получить продукт с названиями типа и материала"""
        return db.query(Product)\
            .join(ProductType, Product.product_type_id == ProductType.id)\
            .join(MaterialType, Product.material_id == MaterialType.id)\
            .filter(Product.id == product_id)\
            .first()
    
    @staticmethod
    def get_by_id(db: Session, product_id: int):
        """Получить продукт по ID"""
        return db.query(Product).filter(Product.id == product_id).first()
    
    @staticmethod
    def create(db: Session, product_data: ProductCreate):
        """Создать новый продукт"""
        # Проверяем существование связанных записей
        product_type = db.query(ProductType).filter(ProductType.id == product_data.product_type_id).first()
        if not product_type:
            raise HTTPException(status_code=400, detail="Тип продукции не найден")
        
        material = db.query(MaterialType).filter(MaterialType.id == product_data.material_id).first()
        if not material:
            raise HTTPException(status_code=400, detail="Материал не найден")
        
        # Проверяем уникальность артикула (опционально, по ТЗ не обязательно)
        existing_product = db.query(Product).filter(Product.article == product_data.article).first()
        if existing_product:
            raise HTTPException(status_code=400, detail="Продукт с таким артикулом уже существует")
        
        try:
            product = Product(**product_data.dict())
            db.add(product)
            db.commit()
            db.refresh(product)
            return product
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Ошибка целостности данных: {str(e)}")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при создании продукта: {str(e)}")
    
    @staticmethod
    def update(db: Session, product_id: int, product_data: ProductUpdate):
        """Обновить продукт"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None
        
        # Проверяем существование связанных записей, если они обновляются
        update_data = product_data.dict(exclude_unset=True)
        
        if 'product_type_id' in update_data:
            product_type = db.query(ProductType).filter(ProductType.id == update_data['product_type_id']).first()
            if not product_type:
                raise HTTPException(status_code=400, detail="Тип продукции не найден")
        
        if 'material_id' in update_data:
            material = db.query(MaterialType).filter(MaterialType.id == update_data['material_id']).first()
            if not material:
                raise HTTPException(status_code=400, detail="Материал не найден")
        
        # Проверяем уникальность артикула, если он обновляется
        if 'article' in update_data and update_data['article'] != product.article:
            existing_product = db.query(Product).filter(Product.article == update_data['article']).first()
            if existing_product:
                raise HTTPException(status_code=400, detail="Продукт с таким артикулом уже существует")
        
        try:
            for field, value in update_data.items():
                if value is not None:
                    setattr(product, field, value)
            
            db.commit()
            db.refresh(product)
            return product
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при обновлении продукта: {str(e)}")
    
    @staticmethod
    def delete(db: Session, product_id: int):
        """Удалить продукт"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False
        
        try:
            db.delete(product)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при удалении продукта: {str(e)}")

# Создаем экземпляр для использования
product_crud = ProductCRUD()