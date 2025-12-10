import os
from pathlib import Path

# Базовый путь проекта
BASE_DIR = Path(__file__).parent.parent

# Пути к данным
DATA_DIR = BASE_DIR / "data"
SOURCE_DATA_DIR = DATA_DIR / "isxod"

# Путь к базе данных
DATABASE_PATH = BASE_DIR / "app" / "database" / "furniture.db"

# Создаем директории, если их нет
SOURCE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Файлы Excel
EXCEL_FILES = {
    'material_types': SOURCE_DATA_DIR / 'Material_type_import.xlsx',
    'product_types': SOURCE_DATA_DIR / 'Product_type_import.xlsx',
    'workshops': SOURCE_DATA_DIR / 'Workshops_import.xlsx',
    'products': SOURCE_DATA_DIR / 'Products_import.xlsx',
    'product_workshop': SOURCE_DATA_DIR / 'Product_workshops_import.xlsx',
}


