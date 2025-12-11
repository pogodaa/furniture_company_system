"""
Эндпоинты для продукции
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.crud.products import product_crud
from app.services.production_time import calculate_total_production_time
from app.schemas.product import ProductResponse, ProductCreate, ProductUpdate

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
            product_with_details = product_crud.get_with_details(db, db_product.id)
            
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
    product = product_crud.get_with_details(db, product_id)
    
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


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Создать новый продукт
    
    - **article**: Артикул продукта
    - **name**: Наименование продукта  
    - **product_type_id**: ID типа продукции
    - **material_id**: ID материала
    - **min_partner_price**: Минимальная стоимость для партнера (до сотых)
    """
    # Создаем продукт
    product = product_crud.create(db, product_data)
    
    # Получаем созданный продукт с деталями
    product_with_details = product_crud.get_with_details(db, product.id)
    
    if not product_with_details:
        raise HTTPException(status_code=500, detail="Ошибка при получении созданного продукта")
    
    # Рассчитываем время изготовления (пока 0, так как нет цехов)
    production_time = 0
    
    return ProductResponse(
        id=product.id,
        product_type=product_with_details.product_type.name,
        product_name=product_with_details.name,
        production_time=production_time,
        article=product_with_details.article,
        min_partner_price=product_with_details.min_partner_price,
        main_material=product_with_details.material.name
    )


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Обновить продукт по ID
    
    Все поля опциональны. Обновляются только переданные поля.
    """
    # Обновляем продукт
    product = product_crud.update(db, product_id, product_data)
    
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Получаем обновленный продукт с деталями
    product_with_details = product_crud.get_with_details(db, product_id)
    
    # Рассчитываем время изготовления
    production_time = calculate_total_production_time(db, product_id)
    
    return ProductResponse(
        id=product.id,
        product_type=product_with_details.product_type.name,
        product_name=product_with_details.name,
        production_time=production_time,
        article=product_with_details.article,
        min_partner_price=product_with_details.min_partner_price,
        main_material=product_with_details.material.name
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Удалить продукт по ID
    
    Внимание: Это действие невозможно отменить!
    """
    success = product_crud.delete(db, product_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Возвращаем пустой ответ со статусом 204
    return None