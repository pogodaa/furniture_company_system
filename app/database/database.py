
from sqlalchemy import (
    create_engine, String, Float, Integer, 
    ForeignKey, Table, Column, event
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, 
    mapped_column, relationship, Session
)
from typing import List
import logging
from pathlib import Path

# Путь к базе данных
DB_PATH = Path(__file__).parent / "furniture.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Создаем движок SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Показывает SQL запросы (удобно для отладки)
    connect_args={"check_same_thread": False}
)

# Настройка SQLite
@event.listens_for(engine, "connect")
def setup_sqlite(dbapi_connection, connection_record):
    """Настройка SQLite при подключении"""
    cursor = dbapi_connection.cursor()
    # ВКЛЮЧАЕМ внешние ключи (обязательно для SQLite!)
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Пробуем включить строгий режим (если версия поддерживает)
    try:
        cursor.execute("PRAGMA strict = ON")
        logging.info("SQLite strict mode enabled")
    except:
        logging.warning("SQLite version doesn't support strict mode")
    
    cursor.close()

# Базовый класс для всех моделей
class Base(DeclarativeBase):
    pass        # Pass потому что нет общих полей, не нужны кастомные типы данных, не нужны общие методы для всех моделей и в целом всё работает и так)

# Таблица связи многие-ко-многим
product_workshop_table = Table(
    "product_workshop",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("product_id", Integer, 
           ForeignKey("products.id", ondelete="CASCADE"), 
           nullable=False),
    Column("workshop_id", Integer, 
           ForeignKey("workshops.id", ondelete="CASCADE"), 
           nullable=False),
    Column("manufacturing_time_hours", Float, 
           nullable=False, default=0.0)
)

# Модель: Тип материала
class MaterialType(Base):
    __tablename__ = "material_types"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    loss_percentage: Mapped[float] = mapped_column(Float, nullable=False)  # 0.8% = 0.008
    
    # Связи
    products: Mapped[List["Product"]] = relationship("Product", back_populates="material")
    
    def __repr__(self):
        return f"MaterialType(id={self.id}, name={self.name})"

# Модель: Тип продукции
class ProductType(Base):
    __tablename__ = "product_types"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    coefficient: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Связи
    products: Mapped[List["Product"]] = relationship("Product", back_populates="product_type")
    
    def __repr__(self):
        return f"ProductType(id={self.id}, name={self.name})"

# Модель: Цех
class Workshop(Base):
    __tablename__ = "workshops"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    workshop_type: Mapped[str] = mapped_column(String(50), nullable=False)
    employee_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Связь многие-ко-многим
    products: Mapped[List["Product"]] = relationship(
        "Product",
        secondary=product_workshop_table,
        back_populates="workshops"
    )
    
    def __repr__(self):
        return f"Workshop(id={self.id}, name={self.name})"

# Модель: Продукт
class Product(Base):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Внешние ключи
    product_type_id: Mapped[int] = mapped_column(
        ForeignKey("product_types.id", ondelete="RESTRICT"), 
        nullable=False
    )
    material_id: Mapped[int] = mapped_column(
        ForeignKey("material_types.id", ondelete="RESTRICT"), 
        nullable=False
    )
    
    min_partner_price: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Связи
    product_type: Mapped[ProductType] = relationship("ProductType", back_populates="products")
    material: Mapped[MaterialType] = relationship("MaterialType", back_populates="products")
    
    # Связь многие-ко-многим
    workshops: Mapped[List[Workshop]] = relationship(
        "Workshop",
        secondary=product_workshop_table,
        back_populates="products"
    )
    
    def __repr__(self):
        return f"Product(id={self.id}, name={self.name}, article={self.article})"

# Функция для создания таблиц
def create_all_tables():
    """Создает все таблицы в базе данных"""
    Base.metadata.create_all(bind=engine)
    print("Все таблицы созданы")

# Функция для получения сессии
def get_session():
    """Возвращает сессию для работы с БД"""
    return Session(engine)