"""
Основное приложение - объединяет API и фронтенд
"""
import sys
from pathlib import Path
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Получаем путь к папке app
BASE_DIR = Path(__file__).parent

# Создаем приложение
app = FastAPI(
    title="Мебельная компания - Система учета",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Подключаем статические файлы фронтенда
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend/static")), name="static")

# Настраиваем шаблонизатор
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend/templates"))

# Импортируем существующие модули
from app.api.config_fastapi import config
from app.api.routers import router as api_router
from app.database.session import get_db

# Подключаем API роутер с префиксом /api
app.include_router(api_router, prefix="/api")

# =========== ФРОНТЕНД РОУТЫ ===========

@app.get("/", response_class=HTMLResponse)
def frontend_index(request: Request):
    """Главная страница фронтенда"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Главная"}
    )

# =========== ПРОДУКЦИЯ ===========

@app.get("/products", response_class=HTMLResponse)
def products_page(
    request: Request,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Страница списка продукции"""
    from app.crud.products import product_crud
    from app.services.production_time import calculate_total_production_time
    
    skip = (page - 1) * limit
    
    # Используем существующую логику из API
    products_response = []
    db_products = product_crud.get_all(db, skip, limit)
    
    for db_product in db_products:
        try:
            product_with_details = product_crud.get_with_details(db, db_product.id)
            if product_with_details:
                production_time = calculate_total_production_time(db, db_product.id)
                
                products_response.append({
                    "id": db_product.id,
                    "product_type": product_with_details.product_type.name,
                    "product_name": product_with_details.name,
                    "production_time": production_time,
                    "article": product_with_details.article,
                    "min_partner_price": product_with_details.min_partner_price,
                    "main_material": product_with_details.material.name
                })
        except Exception as e:
            print(f"Ошибка обработки продукта {db_product.id}: {e}")
            continue
    
    has_next = len(products_response) == limit
    
    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "title": "Продукция",
            "products": products_response,
            "page": page,
            "has_next": has_next
        }
    )

@app.get("/products/add", response_class=HTMLResponse)
def add_product_form(request: Request, db: Session = Depends(get_db)):
    """Форма добавления продукта"""
    from app.crud.product_types import product_type_crud
    from app.crud.material_types import material_type_crud
    
    product_types = product_type_crud.get_all(db)
    material_types = material_type_crud.get_all(db)
    
    return templates.TemplateResponse(
        "product_form.html",
        {
            "request": request,
            "title": "Добавить продукт",
            "product": None,
            "product_types": product_types,
            "material_types": material_types
        }
    )

@app.post("/products/add")
def add_product_submit(
    request: Request,
    article: str = Form(...),
    name: str = Form(...),
    product_type_id: int = Form(...),
    material_id: int = Form(...),
    min_partner_price: float = Form(...),
    db: Session = Depends(get_db)
):
    """Обработка добавления продукта"""
    from app.crud.products import product_crud
    from app.schemas.product import ProductCreate
    
    product_data = ProductCreate(
        article=article,
        name=name,
        product_type_id=product_type_id,
        material_id=material_id,
        min_partner_price=min_partner_price
    )
    
    try:
        product_crud.create(db, product_data)
        return RedirectResponse("/products", status_code=303)
    except Exception as e:
        from app.crud.product_types import product_type_crud
        from app.crud.material_types import material_type_crud
        
        product_types = product_type_crud.get_all(db)
        material_types = material_type_crud.get_all(db)
        
        return templates.TemplateResponse(
            "product_form.html",
            {
                "request": request,
                "title": "Добавить продукт",
                "product": None,
                "product_types": product_types,
                "material_types": material_types,
                "error": f"Ошибка при добавлении: {str(e)}"
            }
        )

@app.get("/products/edit/{product_id}", response_class=HTMLResponse)
def edit_product_form(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db)
):
    """Форма редактирования продукта"""
    from app.crud.products import product_crud
    from app.crud.product_types import product_type_crud
    from app.crud.material_types import material_type_crud
    
    product = product_crud.get_by_id(db, product_id)
    if not product:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Ошибка",
                "status_code": 404,
                "error_title": "Продукт не найден",
                "error_detail": f"Продукт с ID {product_id} не существует"
            }
        )
    
    product_with_details = product_crud.get_with_details(db, product_id)
    product_types = product_type_crud.get_all(db)
    material_types = material_type_crud.get_all(db)
    
    product_data = {
        "id": product.id,
        "article": product.article,
        "product_name": product.name,
        "product_type_id": product.product_type_id,
        "material_id": product.material_id,
        "min_partner_price": product.min_partner_price
    }
    
    return templates.TemplateResponse(
        "product_form.html",
        {
            "request": request,
            "title": "Редактировать продукт",
            "product": product_data,
            "product_types": product_types,
            "material_types": material_types
        }
    )

@app.post("/products/edit/{product_id}")
def edit_product_submit(
    request: Request,
    product_id: int,
    article: str = Form(...),
    name: str = Form(...),
    product_type_id: int = Form(...),
    material_id: int = Form(...),
    min_partner_price: float = Form(...),
    db: Session = Depends(get_db)
):
    """Обработка редактирования продукта"""
    from app.crud.products import product_crud
    from app.schemas.product import ProductUpdate
    
    product_data = ProductUpdate(
        article=article,
        name=name,
        product_type_id=product_type_id,
        material_id=material_id,
        min_partner_price=min_partner_price
    )
    
    try:
        product_crud.update(db, product_id, product_data)
        return RedirectResponse("/products", status_code=303)
    except Exception as e:
        from app.crud.product_types import product_type_crud
        from app.crud.material_types import material_type_crud
        
        product_types = product_type_crud.get_all(db)
        material_types = material_type_crud.get_all(db)
        
        return templates.TemplateResponse(
            "product_form.html",
            {
                "request": request,
                "title": "Редактировать продукт",
                "product": {
                    "id": product_id,
                    "article": article,
                    "product_name": name,
                    "product_type_id": product_type_id,
                    "material_id": material_id,
                    "min_partner_price": min_partner_price
                },
                "product_types": product_types,
                "material_types": material_types,
                "error": f"Ошибка при обновлении: {str(e)}"
            }
        )

@app.get("/products/{product_id}", response_class=HTMLResponse)
def product_detail_page(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db)
):
    """Страница деталей продукта"""
    from app.crud.products import product_crud
    from app.services.production_time import calculate_total_production_time
    from app.database.database import product_workshop_table, Workshop
    from sqlalchemy import select
    
    # Получаем продукт с деталями
    product = product_crud.get_with_details(db, product_id)
    if not product:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Ошибка",
                "status_code": 404,
                "error_title": "Продукт не найден",
                "error_detail": f"Продукт с ID {product_id} не существует"
            }
        )
    
    # Рассчитываем время производства
    production_time = calculate_total_production_time(db, product_id)
    
    # Получаем цеха где производится продукт
    workshops_data = db.execute(
        select(
            product_workshop_table.c.product_id,
            Workshop.id,
            Workshop.name,
            Workshop.workshop_type,
            Workshop.employee_count,
            product_workshop_table.c.manufacturing_time_hours
        )
        .select_from(product_workshop_table)
        .join(Workshop, Workshop.id == product_workshop_table.c.workshop_id)
        .where(product_workshop_table.c.product_id == product_id)
    ).fetchall()
    
    workshops_list = []
    for prod_id, w_id, name, w_type, emp_count, time in workshops_data:
        workshops_list.append({
            "workshop_id": w_id,
            "workshop_name": name,
            "workshop_type": w_type,
            "employee_count": emp_count,
            "manufacturing_time_hours": float(time) if time else 0.0
        })
    
    # Формируем данные продукта для шаблона
    product_data = {
        "id": product.id,
        "product_type": product.product_type.name,
        "product_name": product.name,
        "production_time": production_time,
        "article": product.article,
        "min_partner_price": product.min_partner_price,
        "main_material": product.material.name
    }
    
    return templates.TemplateResponse(
        "product_detail.html",
        {
            "request": request,
            "title": f"Продукт: {product.name}",
            "product": product_data,
            "workshops": workshops_list,
            "total_workshops": len(workshops_list),
            "total_employees": sum(w["employee_count"] for w in workshops_list)
        }
    )

@app.post("/products/delete/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Удаление продукта"""
    from app.crud.products import product_crud
    product_crud.delete(db, product_id)
    return RedirectResponse("/products", status_code=303)

# =========== ЦЕХА ===========

@app.get("/workshops", response_class=HTMLResponse)
def workshops_page(request: Request, db: Session = Depends(get_db)):
    """Страница списка цехов"""
    from app.crud.workshops import workshop_crud
    
    workshops = workshop_crud.get_all(db)
    
    return templates.TemplateResponse(
        "workshops.html",
        {
            "request": request,
            "title": "Цеха",
            "workshops": workshops
        }
    )

@app.get("/workshops/add", response_class=HTMLResponse)
def add_workshop_form(request: Request):
    """Форма добавления цеха"""
    return templates.TemplateResponse(
        "workshop_form.html",
        {
            "request": request,
            "title": "Добавить цех",
            "workshop": None
        }
    )

@app.post("/workshops/add")
def add_workshop_submit(
    request: Request,
    name: str = Form(...),
    workshop_type: str = Form(...),
    employee_count: int = Form(...),
    db: Session = Depends(get_db)
):
    """Обработка добавления цеха"""
    from app.crud.workshops import workshop_crud
    from app.schemas.workshop import WorkshopCreate
    
    workshop_data = WorkshopCreate(
        name=name,
        workshop_type=workshop_type,
        employee_count=employee_count
    )
    
    try:
        workshop_crud.create(db, workshop_data)
        return RedirectResponse("/workshops", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "workshop_form.html",
            {
                "request": request,
                "title": "Добавить цех",
                "workshop": None,
                "error": f"Ошибка при добавлении: {str(e)}"
            }
        )

@app.get("/workshops/edit/{workshop_id}", response_class=HTMLResponse)
def edit_workshop_form(
    request: Request,
    workshop_id: int,
    db: Session = Depends(get_db)
):
    """Форма редактирования цеха"""
    from app.crud.workshops import workshop_crud
    
    workshop = workshop_crud.get_by_id(db, workshop_id)
    if not workshop:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Ошибка",
                "status_code": 404,
                "error_title": "Цех не найден",
                "error_detail": f"Цех с ID {workshop_id} не существует"
            }
        )
    
    workshop_data = {
        "id": workshop.id,
        "name": workshop.name,
        "workshop_type": workshop.workshop_type,
        "employee_count": workshop.employee_count
    }
    
    return templates.TemplateResponse(
        "workshop_form.html",
        {
            "request": request,
            "title": "Редактировать цех",
            "workshop": workshop_data
        }
    )

@app.post("/workshops/edit/{workshop_id}")
def edit_workshop_submit(
    request: Request,
    workshop_id: int,
    name: str = Form(...),
    workshop_type: str = Form(...),
    employee_count: int = Form(...),
    db: Session = Depends(get_db)
):
    """Обработка редактирования цеха"""
    from app.crud.workshops import workshop_crud
    from app.schemas.workshop import WorkshopUpdate
    
    workshop_data = WorkshopUpdate(
        name=name,
        workshop_type=workshop_type,
        employee_count=employee_count
    )
    
    try:
        workshop_crud.update(db, workshop_id, workshop_data)
        return RedirectResponse("/workshops", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "workshop_form.html",
            {
                "request": request,
                "title": "Редактировать цех",
                "workshop": {
                    "id": workshop_id,
                    "name": name,
                    "workshop_type": workshop_type,
                    "employee_count": employee_count
                },
                "error": f"Ошибка при обновлении: {str(e)}"
            }
        )

@app.get("/workshops/{workshop_id}", response_class=HTMLResponse)
def workshop_detail_page(
    request: Request,
    workshop_id: int,
    db: Session = Depends(get_db)
):
    """Детали цеха"""
    from app.crud.workshops import workshop_crud
    from app.database.database import Product, product_workshop_table
    from sqlalchemy import select
    
    workshop = workshop_crud.get_by_id(db, workshop_id)
    if not workshop:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Ошибка",
                "status_code": 404,
                "error_title": "Цех не найден",
                "error_detail": f"Цех с ID {workshop_id} не существует"
            }
        )
    
    # Получаем продукты цеха с деталями
    from app.database.database import ProductType, MaterialType
    products_data = db.execute(
        select(
            product_workshop_table.c.product_id,
            Product.name,
            Product.article,
            Product.min_partner_price,
            ProductType.name.label("product_type_name"),
            MaterialType.name.label("material_name"),
            product_workshop_table.c.manufacturing_time_hours
        )
        .select_from(product_workshop_table)
        .join(Product, Product.id == product_workshop_table.c.product_id)
        .join(ProductType, ProductType.id == Product.product_type_id)
        .join(MaterialType, MaterialType.id == Product.material_id)
        .where(product_workshop_table.c.workshop_id == workshop_id)
    ).fetchall()
    
    # Форматируем продукты
    products_list = []
    for prod_id, name, article, price, type_name, material_name, time in products_data:
        products_list.append({
            "product_id": prod_id,
            "name": name,
            "article": article,
            "min_partner_price": price,
            "product_type_name": type_name,
            "material_name": material_name,
            "manufacturing_time_hours": float(time) if time else 0.0
        })
    
    # Получаем отчет
    total_hours = sum(p["manufacturing_time_hours"] for p in products_list)
    
    return templates.TemplateResponse(
        "workshop_detail.html",
        {
            "request": request,
            "title": f"Цех: {workshop.name}",
            "workshop": workshop,
            "products": products_list,
            "report": {
                "production_data": {
                    "total_products": len(products_list),
                    "total_manufacturing_hours": round(total_hours, 2),
                    "average_hours_per_product": round(
                        total_hours / len(products_list) if products_list else 0, 
                        2
                    ),
                    "employee_productivity": round(
                        total_hours / workshop.employee_count if workshop.employee_count > 0 else 0,
                        2
                    )
                }
            }
        }
    )

@app.get("/workshops/{workshop_id}/products", response_class=HTMLResponse)
def workshop_products_page(
    request: Request,
    workshop_id: int,
    db: Session = Depends(get_db)
):
    """Страница продукции цеха"""
    from app.crud.workshops import workshop_crud
    from app.database.database import Product, product_workshop_table, ProductType, MaterialType
    from sqlalchemy import select
    
    workshop = workshop_crud.get_by_id(db, workshop_id)
    if not workshop:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Ошибка",
                "status_code": 404,
                "error_title": "Цех не найден",
                "error_detail": f"Цех с ID {workshop_id} не существует"
            }
        )
    
    # Получаем продукты цеха с деталями
    products_data = db.execute(
        select(
            product_workshop_table.c.product_id,
            Product.name,
            Product.article,
            Product.min_partner_price,
            ProductType.name.label("product_type_name"),
            MaterialType.name.label("material_name"),
            product_workshop_table.c.manufacturing_time_hours
        )
        .select_from(product_workshop_table)
        .join(Product, Product.id == product_workshop_table.c.product_id)
        .join(ProductType, ProductType.id == Product.product_type_id)
        .join(MaterialType, MaterialType.id == Product.material_id)
        .where(product_workshop_table.c.workshop_id == workshop_id)
    ).fetchall()
    
    # Форматируем продукты
    products_list = []
    for prod_id, name, article, price, type_name, material_name, time in products_data:
        products_list.append({
            "id": prod_id,
            "name": name,
            "article": article,
            "min_partner_price": price,
            "product_type_name": type_name,
            "material_name": material_name,
            "manufacturing_time_hours": float(time) if time else 0.0
        })
    
    return templates.TemplateResponse(
        "workshop_products.html",
        {
            "request": request,
            "title": f"Продукция цеха: {workshop.name}",
            "workshop": workshop,
            "products": products_list
        }
    )

@app.post("/workshops/delete/{workshop_id}")
def delete_workshop(
    workshop_id: int,
    db: Session = Depends(get_db)
):
    """Удаление цеха"""
    from app.crud.workshops import workshop_crud
    workshop_crud.delete(db, workshop_id)
    return RedirectResponse("/workshops", status_code=303)

# =========== РАСЧЕТЫ ===========

@app.get("/calculations", response_class=HTMLResponse)
def calculations_page(request: Request, db: Session = Depends(get_db)):
    """Страница расчета сырья"""
    try:
        # Используем прямые SQLAlchemy запросы вместо CRUD
        from app.database.database import ProductType, MaterialType
        
        # Получаем типы продукции
        product_types = db.query(ProductType).all()
        # Преобразуем в список словарей для шаблона
        product_types_list = [
            {
                "id": pt.id,
                "name": pt.name,
                "coefficient": pt.coefficient
            }
            for pt in product_types
        ]
        
        # Получаем типы материалов
        material_types = db.query(MaterialType).all()
        # Преобразуем в список словарей для шаблона
        material_types_list = [
            {
                "id": mt.id,
                "name": mt.name,
                "loss_percentage": mt.loss_percentage
            }
            for mt in material_types
        ]
        
        return templates.TemplateResponse(
            "calculations.html",
            {
                "request": request,
                "title": "Расчет сырья",
                "product_types": product_types_list,
                "material_types": material_types_list,
                "result": None
            }
        )
    except Exception as e:
        import traceback
        print(f"Ошибка в calculations_page: {e}")
        traceback.print_exc()
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "title": "Ошибка сервера",
                "status_code": 500,
                "error_title": "Внутренняя ошибка сервера",
                "error_detail": f"Не удалось загрузить страницу расчетов: {str(e)}"
            }
        )

@app.post("/calculations")
def calculate_raw_material_submit(
    request: Request,
    product_type_id: int = Form(...),
    material_type_id: int = Form(...),
    product_quantity: int = Form(...),
    param1: float = Form(...),
    param2: float = Form(...),
    db: Session = Depends(get_db)
):
    """Обработка расчета сырья"""
    try:
        print(f"Получены данные для расчета: product_type_id={product_type_id}, "
              f"material_type_id={material_type_id}, quantity={product_quantity}, "
              f"param1={param1}, param2={param2}")
        
        # Используем прямые SQLAlchemy запросы для справочников
        from app.database.database import ProductType, MaterialType
        
        # Получаем справочники для формы
        product_types = db.query(ProductType).all()
        material_types = db.query(MaterialType).all()
        
        # Преобразуем в список словарей
        product_types_list = [
            {
                "id": pt.id,
                "name": pt.name,
                "coefficient": pt.coefficient
            }
            for pt in product_types
        ]
        
        material_types_list = [
            {
                "id": mt.id,
                "name": mt.name,
                "loss_percentage": mt.loss_percentage
            }
            for mt in material_types
        ]
        
        try:
            from app.services.raw_material_calculation import calculate_raw_material_with_details
            
            # Выполняем расчет
            print("Вызываем calculate_raw_material_with_details...")
            result, details = calculate_raw_material_with_details(
                db=db,
                product_type_id=product_type_id,
                material_type_id=material_type_id,
                product_quantity=product_quantity,
                param1=param1,
                param2=param2
            )
            print(f"Результат расчета: {result}")
            print(f"Детали расчета: {details}")
            
        except ImportError as e:
            print(f"Ошибка импорта calculate_raw_material_with_details: {e}")
            # Если функция недоступна, делаем простой расчет
            result, details = -1, None
            
        except Exception as e:
            print(f"Ошибка в calculate_raw_material_with_details: {e}")
            import traceback
            traceback.print_exc()
            result, details = -1, None
        
        if result == -1 or details is None:
            print("Расчет не удался, возвращаем форму с ошибкой")
            # Попробуем сделать простой расчет вручную
            try:
                # Прямой запрос к базе для проверки
                product_type = db.query(ProductType).filter(ProductType.id == product_type_id).first()
                material_type = db.query(MaterialType).filter(MaterialType.id == material_type_id).first()
                
                if product_type and material_type:
                    import math
                    params_product = param1 * param2
                    material_per_unit = params_product * product_type.coefficient
                    total_without_loss = material_per_unit * product_quantity
                    loss_factor = 1 + (material_type.loss_percentage / 100)
                    total_with_loss = total_without_loss * loss_factor
                    total_rounded = math.ceil(total_with_loss)
                    
                    result = total_rounded
                    details = {
                        "product_type_name": product_type.name,
                        "material_name": material_type.name,
                        "coefficient": product_type.coefficient,
                        "loss_percentage": material_type.loss_percentage,
                        "product_quantity": product_quantity,
                        "param1": param1,
                        "param2": param2,
                        "params_product": params_product,
                        "material_per_unit": material_per_unit,
                        "total_without_loss": total_without_loss,
                        "loss_factor": loss_factor,
                        "total_with_loss": total_with_loss,
                        "total_rounded": total_rounded
                    }
                    print(f"Ручной расчет успешен: {result}")
                else:
                    print("Не найдены product_type или material_type в БД")
                    
            except Exception as calc_error:
                print(f"Ошибка в ручном расчете: {calc_error}")
                return templates.TemplateResponse(
                    "calculations.html",
                    {
                        "request": request,
                        "title": "Расчет сырья",
                        "product_types": product_types_list,
                        "material_types": material_types_list,
                        "error": f"Ошибка при расчете: {str(calc_error)}"
                    }
                )
        
        print("Возвращаем результат...")
        return templates.TemplateResponse(
            "calculations.html",
            {
                "request": request,
                "title": "Расчет сырья",
                "product_types": product_types_list,
                "material_types": material_types_list,
                "result": {
                    "raw_material_quantity": result,
                    "product_type_id": product_type_id,
                    "material_type_id": material_type_id,
                    "product_quantity": product_quantity,
                    "param1": param1,
                    "param2": param2,
                    "calculation_details": details
                }
            }
        )
        
    except Exception as e:
        import traceback
        print(f"Общая ошибка в calculate_raw_material_submit: {e}")
        traceback.print_exc()
        
        try:
            # Пытаемся получить справочники для показа формы с ошибкой
            from app.database.database import ProductType, MaterialType
            product_types = db.query(ProductType).all()
            material_types = db.query(MaterialType).all()
            
            product_types_list = [
                {
                    "id": pt.id,
                    "name": pt.name,
                    "coefficient": pt.coefficient
                }
                for pt in product_types
            ]
            
            material_types_list = [
                {
                    "id": mt.id,
                    "name": mt.name,
                    "loss_percentage": mt.loss_percentage
                }
                for mt in material_types
            ]
        except:
            product_types_list = []
            material_types_list = []
        
        return templates.TemplateResponse(
            "calculations.html",
            {
                "request": request,
                "title": "Расчет сырья",
                "product_types": product_types_list,
                "material_types": material_types_list,
                "error": f"Ошибка при расчете: {str(e)}"
            }
        )

# =========== ОБРАБОТЧИКИ ОШИБОК ===========

@app.exception_handler(404)
def not_found_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "title": "Страница не найдена",
            "status_code": 404,
            "error_title": "Страница не найдена",
            "error_detail": "Запрошенная страница не существует."
        }
    )

# =========== HEALTH CHECKS ===========

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "furniture-system-combined"}

@app.get("/api/health")
def api_health_check():
    return {"status": "ok", "service": "furniture-api"}

# =========== ЗАПУСК ===========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=config.reload
    )