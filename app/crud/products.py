from sqlalchemy.orm import Session
from app.database.database import Product, ProductType, MaterialType
from app.schemas.product import ProductCreate

class ProductCRUD:
    """Простейший CRUD для продукции"""
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        """Получить все продукты (просто)"""
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
    def create(db: Session, product_data: ProductCreate):
        """Создать новый продукт"""
        product = Product(**product_data.dict())
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    
    @staticmethod
    def get_by_id(db: Session, product_id: int):
      """Получить продукт по ID"""
      return db.query(Product)\
        .join(ProductType, Product.product_type_id == ProductType.id)\
        .join(MaterialType, Product.material_id == MaterialType.id)\
        .filter(Product.id == product_id)\
        .first()

    @staticmethod
    def update(db: Session, product_id: int, product_data: dict):
      """Обновить продукт"""
      product = db.query(Product).filter(Product.id == product_id).first()
      if not product:
        return None
    
      for field, value in product_data.items():
            if value is not None:
                  setattr(product, field, value)
    
      db.commit()
      db.refresh(product)
      return product

    @staticmethod
    def delete(db: Session, product_id: int):
      """Удалить продукт"""
      product = db.query(Product).filter(Product.id == product_id).first()
      if product:
            db.delete(product)
            db.commit()
            return True
      
      return False

# Создаем экземпляр для использования
product_crud = ProductCRUD()