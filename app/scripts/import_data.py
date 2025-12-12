
import sys
import os
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional, Union

# Добавляем корневую директорию в путь Python
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Теперь можем импортировать модули проекта
from app.database import (
    engine, get_session, create_all_tables,
    MaterialType, ProductType, Workshop, Product, product_workshop_table
)
from app.config import EXCEL_FILES

import pandas as pd
from sqlalchemy import select
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('import.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DataTypeValidator:
    """Класс для валидации типов данных"""
    
    @staticmethod
    def validate_string(value: Any, field_name: str, max_length: Optional[int] = None) -> str:
        """Валидация строковых значений"""
        if pd.isna(value) or value is None:
            raise ValueError(f"Поле '{field_name}' не может быть пустым")
        
        result = str(value).strip()
        
        if not result:
            raise ValueError(f"Поле '{field_name}' не может быть пустой строкой")
        
        if max_length and len(result) > max_length:
            raise ValueError(
                f"Поле '{field_name}' слишком длинное: {len(result)} символов "
                f"(максимум {max_length})"
            )
        
        return result
    
    @staticmethod
    def validate_integer(value: Any, field_name: str, min_value: Optional[int] = None, 
                         max_value: Optional[int] = None) -> int:
        """Валидация целых чисел"""
        if pd.isna(value) or value is None:
            raise ValueError(f"Поле '{field_name}' не может быть пустым")
        
        # Преобразуем строку с разделителями
        if isinstance(value, str):
            value = value.replace(' ', '').replace(',', '').strip()
        
        try:
            # Пробуем преобразовать в int
            if isinstance(value, float) and value.is_integer():
                result = int(value)
            else:
                result = int(float(value))
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Поле '{field_name}': не удалось преобразовать '{value}' в целое число"
            ) from e
        
        # Проверка диапазона
        if min_value is not None and result < min_value:
            raise ValueError(
                f"Поле '{field_name}': значение {result} меньше минимального {min_value}"
            )
        
        if max_value is not None and result > max_value:
            raise ValueError(
                f"Поле '{field_name}': значение {result} больше максимального {max_value}"
            )
        
        return result
    
    @staticmethod
    def validate_float(value: Any, field_name: str, min_value: Optional[float] = None,
                      max_value: Optional[float] = None, precision: int = 2) -> float:
        """Валидация чисел с плавающей точкой"""
        if pd.isna(value) or value is None:
            raise ValueError(f"Поле '{field_name}' не может быть пустым")
        
        # Преобразуем строку с разделителями
        if isinstance(value, str):
            value = value.replace(' ', '').replace(',', '').strip()
        
        try:
            result = float(value)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Поле '{field_name}': не удалось преобразовать '{value}' в число"
            ) from e
        
        # Округляем до указанной точности
        if precision:
            result = float(Decimal(str(result)).quantize(
                Decimal(f"1.{'0' * precision}"), rounding=ROUND_HALF_UP
            ))
        
        # Проверка диапазона
        if min_value is not None and result < min_value:
            raise ValueError(
                f"Поле '{field_name}': значение {result:.{precision}f} "
                f"меньше минимального {min_value}"
            )
        
        if max_value is not None and result > max_value:
            raise ValueError(
                f"Поле '{field_name}': значение {result:.{precision}f} "
                f"больше максимального {max_value}"
            )
        
        return result

    @staticmethod
    def validate_percentage(value: Any, field_name: str) -> float:
        """Валидация процентных значений - храним как проценты (0.8 для 0.8%)"""
        if pd.isna(value) or value is None:
            raise ValueError(f"Поле '{field_name}' не может быть пустым")
        
        original_value = str(value)
        
        # Обрабатываем проценты
        if isinstance(value, str):
            value = value.replace('%', '').strip()
            value = value.replace(',', '.')
        elif isinstance(value, float):
            # Если pandas уже преобразовал 0,80% в 0.008 (доли)
            if value < 0.01:  # Если значение меньше 1% (в долях)
                value = value * 100  # 0.008 → 0.8
        
        try:
            result = float(value)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Поле '{field_name}': не удалось преобразовать '{original_value}' в число"
            ) from e
        
        # ИСПРАВЛЕНИЕ: Проверяем диапазон 0-100 (а не 0-1)
        if result < 0:
            raise ValueError(f"Поле '{field_name}': процент не может быть отрицательным")
        if result > 100:  # 100% максимум (а не 1!)
            raise ValueError(f"Поле '{field_name}': процент не может превышать 100%")
        
        # Округляем до 4 знаков после запятой
        return float(Decimal(str(result)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))
    
    @staticmethod
    def validate_positive_float(value: Any, field_name: str, precision: int = 2) -> float:
        """Валидация положительных чисел"""
        result = DataTypeValidator.validate_float(value, field_name, precision=precision)
        
        if result < 0:
            raise ValueError(f"Поле '{field_name}' не может быть отрицательным")
        
        return result
    
    @staticmethod
    def validate_positive_integer(value: Any, field_name: str) -> int:
        """Валидация положительных целых чисел"""
        result = DataTypeValidator.validate_integer(value, field_name, min_value=1)
        return result

def clean_number(value: Any) -> float:
    """Очистка числовых значений с валидацией"""
    try:
        return DataTypeValidator.validate_float(value, "числовое значение", precision=2)
    except ValueError as e:
        logger.warning(f"Ошибка валидации числа: {e}")
        return 0.0

# def clean_percentage(value: Any) -> float:
#     """Преобразование процентов с валидацией"""
#     try:
#         return DataTypeValidator.validate_percentage(value, "процент")
#     except ValueError as e:
#         logger.warning(f"Ошибка валидации процента: {e}")
#         return 0.0

def clean_percentage(value: Any) -> float:
    """Преобразование процентов с валидацией"""
    try:
        return DataTypeValidator.validate_percentage(value, "процент")
    except ValueError as e:
        logger.warning(f"Ошибка валидации процента: {e}")
        return 0.0

def import_material_types(session):
    """Импорт типов материалов с валидацией"""
    logger.info("Импорт типов материалов...")
    
    file_path = EXCEL_FILES['material_types']
    if not file_path.exists():
        logger.error(f"Файл не найден: {file_path}")
        return
    
    df = pd.read_excel(file_path)
    imported_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Валидация данных
            material_name = DataTypeValidator.validate_string(
                row['Тип материала'], 'Тип материала', max_length=100
            )
            
            loss_percentage = DataTypeValidator.validate_percentage(
                row['Процент потерь сырья'], 'Процент потерь сырья'
            )
            
            # Проверка уникальности имени
            existing = session.query(MaterialType).filter_by(name=material_name).first()
            if existing:
                logger.warning(f"Материал '{material_name}' уже существует, пропускаем")
                continue
            
            material = MaterialType(
                name=material_name,
                loss_percentage=loss_percentage
            )
            session.add(material)
            imported_count += 1
            
            logger.debug(f"Добавлен материал: {material_name} ({loss_percentage:.4f})")
            
        except ValueError as e:
            error_count += 1
            logger.error(f"Строка {idx + 2}: {e}")
        except Exception as e:
            error_count += 1
            logger.error(f"Строка {idx + 2}: Неожиданная ошибка: {e}")
    
    session.commit()
    logger.info(f"Импортировано {imported_count} типов материалов, ошибок: {error_count}")

def import_product_types(session):
    """Импорт типов продукции с валидацией"""
    logger.info("Импорт типов продукции...")
    
    file_path = EXCEL_FILES['product_types']
    if not file_path.exists():
        logger.error(f"Файл не найден: {file_path}")
        return
    
    df = pd.read_excel(file_path)
    imported_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Валидация данных
            type_name = DataTypeValidator.validate_string(
                row['Тип продукции'], 'Тип продукции', max_length=100
            )
            
            coefficient = DataTypeValidator.validate_positive_float(
                row['Коэффициент типа продукции'], 'Коэффициент типа продукции', precision=2
            )
            
            # Проверка уникальности имени
            existing = session.query(ProductType).filter_by(name=type_name).first()
            if existing:
                logger.warning(f"Тип продукции '{type_name}' уже существует, пропускаем")
                continue
            
            product_type = ProductType(
                name=type_name,
                coefficient=coefficient
            )
            session.add(product_type)
            imported_count += 1
            
            logger.debug(f"Добавлен тип продукции: {type_name} (коэфф: {coefficient})")
            
        except ValueError as e:
            error_count += 1
            logger.error(f"Строка {idx + 2}: {e}")
        except Exception as e:
            error_count += 1
            logger.error(f"Строка {idx + 2}: Неожиданная ошибка: {e}")
    
    session.commit()
    logger.info(f"Импортировано {imported_count} типов продукции, ошибок: {error_count}")

def import_workshops(session):
    """Импорт цехов с валидацией"""
    logger.info("Импорт цехов...")
    
    file_path = EXCEL_FILES['workshops']
    if not file_path.exists():
        logger.error(f"Файл не найден: {file_path}")
        return
    
    df = pd.read_excel(file_path)
    
    # Очищаем названия столбцов
    df.columns = df.columns.str.strip()
    
    # Исправляем возможные проблемы с названиями столбцов
    column_mapping = {
        'Количество человек для производства ': 'Количество человек для производства',
        'Количество человек для производства': 'Количество человек для производства',
        'Название цеха': 'Название цеха',
        'Тип цеха': 'Тип цеха'
    }
    
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df = df.rename(columns={old_col: new_col})
    
    imported_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Валидация данных
            workshop_name = DataTypeValidator.validate_string(
                row['Название цеха'], 'Название цеха', max_length=100
            )
            
            workshop_type = DataTypeValidator.validate_string(
                row['Тип цеха'], 'Тип цеха', max_length=50
            )
            
            employee_count = DataTypeValidator.validate_positive_integer(
                row['Количество человек для производства'], 
                'Количество человек для производства'
            )
            
            # Проверка уникальности имени
            existing = session.query(Workshop).filter_by(name=workshop_name).first()
            if existing:
                logger.warning(f"Цех '{workshop_name}' уже существует, пропускаем")
                continue
            
            workshop = Workshop(
                name=workshop_name,
                workshop_type=workshop_type,
                employee_count=employee_count
            )
            session.add(workshop)
            imported_count += 1
            
            logger.debug(f"Добавлен цех: {workshop_name} ({employee_count} чел.)")
            
        except ValueError as e:
            error_count += 1
            logger.error(f"Строка {idx + 2}: {e}")
        except KeyError as e:
            error_count += 1
            logger.error(f"Строка {idx + 2}: Отсутствует столбец: {e}")
        except Exception as e:
            error_count += 1
            logger.error(f"Строка {idx + 2}: Неожиданная ошибка: {e}")
    
    session.commit()
    logger.info(f"Импортировано {imported_count} цехов, ошибок: {error_count}")

def import_products(session):
    """Импорт продукции с валидацией"""
    logger.info("Импорт продукции...")
    
    file_path = EXCEL_FILES['products']
    if not file_path.exists():
        logger.error(f"Файл не найден: {file_path}")
        return
    
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    
    # Получаем словари для маппинга имен на ID
    material_map = {m.name: m.id for m in session.query(MaterialType).all()}
    product_type_map = {pt.name: pt.id for pt in session.query(ProductType).all()}
    
    imported_count = 0
    error_count = 0
    skipped_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Валидация данных
            material_name = DataTypeValidator.validate_string(
                row['Основной материал'], 'Основной материал', max_length=100
            )
            
            product_type_name = DataTypeValidator.validate_string(
                row['Тип продукции'], 'Тип продукции', max_length=100
            )
            
            product_name = DataTypeValidator.validate_string(
                row['Наименование продукции'], 'Наименование продукции', max_length=200
            )
            
            # Артикул - целое число
            article = DataTypeValidator.validate_integer(
                row['Артикул'], 'Артикул', min_value=1
            )
            
            min_price = DataTypeValidator.validate_positive_float(
                row['Минимальная стоимость для партнера'],
                'Минимальная стоимость для партнера',
                precision=2
            )
            
            # Проверяем существование справочников
            if material_name not in material_map:
                skipped_count += 1
                logger.warning(f"Строка {idx + 2}: Материал '{material_name}' не найден, пропускаем")
                continue
            
            if product_type_name not in product_type_map:
                skipped_count += 1
                logger.warning(f"Строка {idx + 2}: Тип продукции '{product_type_name}' не найден, пропускаем")
                continue
            
            # Проверка уникальности артикула
            existing_article = session.query(Product).filter_by(article=str(article)).first()
            if existing_article:
                logger.warning(
                    f"Строка {idx + 2}: Продукт с артикулом '{article}' уже существует "
                    f"('{existing_article.name}'), пропускаем"
                )
                skipped_count += 1
                continue
            
            product = Product(
                article=str(article),  # Храним как строку для гибкости
                name=product_name,
                product_type_id=product_type_map[product_type_name],
                material_id=material_map[material_name],
                min_partner_price=min_price
            )
            session.add(product)
            imported_count += 1
            
            logger.debug(f"Добавлен продукт: {product_name} (арт: {article})")
            
        except ValueError as e:
            error_count += 1
            logger.error(f"Строка {idx + 2}: {e}")
        except KeyError as e:
            error_count += 1
            logger.error(f"Строка {idx + 2}: Отсутствует столбец: {e}")
        except Exception as e:
            error_count += 1
            logger.error(f"Строка {idx + 2}: Неожиданная ошибка: {e}")
    
    session.commit()
    logger.info(
        f"Импортировано {imported_count} продуктов, "
        f"пропущено: {skipped_count}, ошибок: {error_count}"
    )

def import_product_workshop_links(session):
    """Импорт связей продукции и цехов с валидацией"""
    logger.info("Импорт связей продукции и цехов...")
    
    file_path = EXCEL_FILES['product_workshop']
    if not file_path.exists():
        logger.error(f"Файл не найден: {file_path}")
        return
    
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    
    # Получаем словари для маппинга
    product_map = {p.name: p.id for p in session.query(Product).all()}
    workshop_map = {w.name: w.id for w in session.query(Workshop).all()}
    
    imported_count = 0
    error_count = 0
    skipped_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Валидация данных
            product_name = DataTypeValidator.validate_string(
                row['Наименование продукции'], 'Наименование продукции', max_length=200
            )
            
            workshop_name = DataTypeValidator.validate_string(
                row['Название цеха'], 'Название цеха', max_length=100
            )
            
            manufacturing_time = DataTypeValidator.validate_positive_float(
                row['Время изготовления, ч'],
                'Время изготовления',
                precision=1
            )
            
            if product_name not in product_map:
                skipped_count += 1
                logger.warning(f"Строка {idx + 2}: Продукт '{product_name}' не найден, пропускаем")
                continue
            
            if workshop_name not in workshop_map:
                skipped_count += 1
                logger.warning(f"Строка {idx + 2}: Цех '{workshop_name}' не найден, пропускаем")
                continue
            
            # Проверяем, не существует ли уже такая связь
            existing_link = session.execute(
                select(product_workshop_table)
                .where(
                    (product_workshop_table.c.product_id == product_map[product_name]) &
                    (product_workshop_table.c.workshop_id == workshop_map[workshop_name])
                )
            ).fetchone()
            
            if existing_link:
                logger.warning(
                    f"Строка {idx + 2}: Связь продукта '{product_name}' с цехом "
                    f"'{workshop_name}' уже существует, пропускаем"
                )
                skipped_count += 1
                continue
            
            # Добавляем связь во вспомогательную таблицу
            session.execute(
                product_workshop_table.insert().values(
                    product_id=product_map[product_name],
                    workshop_id=workshop_map[workshop_name],
                    manufacturing_time_hours=manufacturing_time
                )
            )
            imported_count += 1
            
            logger.debug(
                f"Добавлена связь: '{product_name}' - '{workshop_name}' "
                f"({manufacturing_time} ч)"
            )
            
        except ValueError as e:
            error_count += 1
            logger.error(f"Строка {idx + 2}: {e}")
        except KeyError as e:
            error_count += 1
            logger.error(f"Строка {idx + 2}: Отсутствует столбец: {e}")
        except Exception as e:
            error_count += 1
            logger.error(f"Строка {idx + 2}: Неожиданная ошибка: {e}")
    
    session.commit()
    logger.info(
        f"Импортировано {imported_count} связей, "
        f"пропущено: {skipped_count}, ошибок: {error_count}"
    )

def main():
    """Основная функция импорта"""
    print("=" * 70)
    print("ИМПОРТ ДАННЫХ В БАЗУ ДАННЫХ С ПРОВЕРКОЙ ТИПОВ")
    print("=" * 70)
    
    # Создаем таблицы
    create_all_tables()
    
    # Открываем сессию
    with get_session() as session:
        try:
            # Порядок импорта ВАЖЕН!
            import_material_types(session)
            import_product_types(session)
            import_workshops(session)
            import_products(session)
            import_product_workshop_links(session)
            
            print("\n" + "=" * 70)
            print("ИМПОРТ УСПЕШНО ЗАВЕРШЕН!")
            print("=" * 70)
            
            # Выводим статистику
            print_statistics(session)
            
            # Предлагаем запустить проверку
            print("\n" + "=" * 70)
            print("РЕКОМЕНДАЦИЯ")
            print("=" * 70)
            print("Запустите проверку корректности импорта:")
            print("python -m app.scripts.validate_import")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Критическая ошибка импорта: {e}", exc_info=True)
            raise

def print_statistics(session):
    """Вывод статистики базы данных"""
    from sqlalchemy import func
    
    print("\nСТАТИСТИКА БАЗЫ ДАННЫХ:")
    print("-" * 40)
    
    tables = [
        ("Типы материалов", MaterialType),
        ("Типы продукции", ProductType),
        ("Цеха", Workshop),
        ("Продукция", Product)
    ]
    
    for name, model in tables:
        count = session.query(func.count(model.id)).scalar()
        print(f"{name}: {count}")
    
    # Считаем связи
    link_count = session.query(func.count(product_workshop_table.c.id)).scalar()
    print(f"Связи продукции-цехов: {link_count}")
    
    # Проверяем типы данных
    print("\n🔍 ПРОВЕРКА ТИПОВ ДАННЫХ:")
    print("-" * 40)
    
    # Проверка отрицательных значений
    negative_prices = session.query(Product).filter(Product.min_partner_price < 0).count()
    print(f"Отрицательных цен: {negative_prices}")
    
    negative_time = session.query(product_workshop_table)\
        .filter(product_workshop_table.c.manufacturing_time_hours < 0)\
        .count()
    print(f"Отрицательного времени: {negative_time}")
    
    # Проверка целостности
    products_without_type = session.query(Product)\
        .filter(~Product.product_type_id.in_(session.query(ProductType.id)))\
        .count()
    print(f"Продуктов без типа: {products_without_type}")
    
    products_without_material = session.query(Product)\
        .filter(~Product.material_id.in_(session.query(MaterialType.id)))\
        .count()
    print(f"Продуктов без материала: {products_without_material}")

if __name__ == "__main__":
    main()