"""
Эндпоинты для продукции
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from typing import List

from app.database.session import get_db
from app.database.database import Product, ProductType, MaterialType, product_workshop_table
from app.crud.products import product_crud
from app.services.production_time import calculate_total_production_time
from app.schemas.product import ProductResponse

# Создаем роутер с префиксом /products
router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/", response_model=List[ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получить список продукции согласно макету
    
    Возвращает:
    - Тип | Наименование продукта | Время изготовления
    - Артикул
    - Минимальная стоимость для партнера
    - Основной материал
    """
    products_response = []
    
    # Получаем продукты из БД
    db_products = product_crud.get_all(db, skip, limit)
    
    for db_product in db_products:
        try:
            # Получаем связанные данные
            product_with_details = db.query(Product)\
                .join(ProductType, Product.product_type_id == ProductType.id)\
                .join(MaterialType, Product.material_id == MaterialType.id)\
                .filter(Product.id == db_product.id)\
                .first()
            
            if product_with_details:
                # Рассчитываем время
                production_time = calculate_total_production_time(db, db_product.id)
                
                # Создаем ответ по макету
                product_response = ProductResponse(
                    id=db_product.id,
                    product_type=product_with_details.product_type.name,
                    product_name=product_with_details.name,
                    production_time=production_time,
                    article=product_with_details.article,
                    min_partner_price=product_with_details.min_partner_price,
                    main_material=product_with_details.material.name
                )
                products_response.append(product_response)
                
        except Exception as e:
            # Пропускаем продукты с ошибками
            print(f"Ошибка обработки продукта {db_product.id}: {e}")
            continue
    
    return products_response


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить один продукт по ID
    """
    # Получаем продукт с связанными данными
    product = db.query(Product)\
        .join(ProductType, Product.product_type_id == ProductType.id)\
        .join(MaterialType, Product.material_id == MaterialType.id)\
        .filter(Product.id == product_id)\
        .first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Рассчитываем время
    production_time = calculate_total_production_time(db, product_id)
    
    return ProductResponse(
        id=product.id,
        product_type=product.product_type.name,
        product_name=product.name,
        production_time=production_time,
        article=product.article,
        min_partner_price=product.min_partner_price,
        main_material=product.material.name
    )