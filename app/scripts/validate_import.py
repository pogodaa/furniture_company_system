
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from app.database import get_session, MaterialType, ProductType, Workshop, Product, product_workshop_table
from app.config import EXCEL_FILES
import pandas as pd
from sqlalchemy import select, func, text, exists, and_
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class ImportValidator:
    """Класс для проверки корректности импорта данных"""
    
    def __init__(self):
        self.session = None
        self.results = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'details': []
        }
    
    def _add_result(self, success: bool, message: str):
        """Добавляет результат проверки"""
        self.results['total_checks'] += 1
        if success:
            self.results['passed_checks'] += 1
            self.results['details'].append(f"{message}")
        else:
            self.results['failed_checks'] += 1
            self.results['details'].append(f"{message}")
    
    def c(self):
        return 0
    
    def check_material_types(self):
        """Проверка типов материалов"""
        logger.info("\n🔍 Проверка типов материалов...")
        
        try:
            # 1. Проверяем количество
            excel_file = EXCEL_FILES['material_types']
            df = pd.read_excel(excel_file)
            excel_count = len(df)
            
            db_count = self.session.query(MaterialType).count()
            
            self._add_result(
                excel_count == db_count,
                f"Типы материалов: совпадение количества (Excel: {excel_count}, БД: {db_count})"
            )
            
            # 2. Проверяем каждую запись
            for _, row in df.iterrows():
                material_name = str(row['Тип материала']).strip()
                
                # Обработка процента как в функции импорта
                loss_percentage = self._convert_percentage(row['Процент потерь сырья'])
                
                material = self.session.query(MaterialType).filter_by(name=material_name).first()
                
                if material:
                    # Допустимая погрешность 0.0001 (0.01%)
                    if abs(material.loss_percentage - loss_percentage) < 0.0001:
                        self._add_result(
                            True, 
                            f"Материал '{material_name}' корректно импортирован "
                            f"({loss_percentage:.4f})"
                        )
                    else:
                        self._add_result(
                            False, 
                            f"Материал '{material_name}': несовпадение процентов "
                            f"(Excel: {loss_percentage:.4f}, БД: {material.loss_percentage:.4f})"
                        )
                else:
                    self._add_result(False, f"Материал '{material_name}' не найден в БД")
                    
        except Exception as e:
            self._add_result(False, f"Ошибка проверки типов материалов: {e}")

    def _convert_percentage(self, value):
        """Конвертирует процентные значения как в функции импорта"""
        if pd.isna(value):
            return 0.0
        
        if isinstance(value, str):
            value = value.replace('%', '').strip()
            # Заменяем запятую на точку
            value = value.replace(',', '.')
        
        try:
            num = float(value)
            # Если число > 1 (например 0.80), делим на 100
            return num / 100 if num > 1 else num
        except:
            return 0.0
    
    def check_product_types(self):
        """Проверка типов продукции"""
        logger.info("\n🔍 Проверка типов продукции...")
        
        try:
            excel_file = EXCEL_FILES['product_types']
            df = pd.read_excel(excel_file)
            excel_count = len(df)
            
            db_count = self.session.query(ProductType).count()
            
            self._add_result(
                excel_count == db_count,
                f"Типы продукции: совпадение количества (Excel: {excel_count}, БД: {db_count})"
            )
            
            for _, row in df.iterrows():
                type_name = str(row['Тип продукции']).strip()
                coefficient = float(row['Коэффициент типа продукции'])
                
                product_type = self.session.query(ProductType).filter_by(name=type_name).first()
                
                if product_type:
                    if abs(product_type.coefficient - coefficient) < 0.01:
                        self._add_result(True, f"Тип продукции '{type_name}' корректно импортирован")
                    else:
                        self._add_result(
                            False,
                            f"Тип продукции '{type_name}': несовпадение коэффициентов "
                            f"(Excel: {coefficient}, БД: {product_type.coefficient})"
                        )
                else:
                    self._add_result(False, f"Тип продукции '{type_name}' не найден в БД")
                    
        except Exception as e:
            self._add_result(False, f"Ошибка проверки типов продукции: {e}")
    
    def check_workshops(self):
        """Проверка цехов"""
        logger.info("\n🔍 Проверка цехов...")
        
        try:
            excel_file = EXCEL_FILES['workshops']
            df = pd.read_excel(excel_file)
            
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
            
            excel_count = len(df)
            db_count = self.session.query(Workshop).count()
            
            self._add_result(
                excel_count == db_count,
                f"Цеха: совпадение количества (Excel: {excel_count}, БД: {db_count})"
            )
            
            # Проверяем несколько записей (первые 5)
            sample_size = min(5, len(df))
            for i in range(sample_size):
                row = df.iloc[i]
                workshop_name = str(row['Название цеха']).strip()
                
                workshop = self.session.query(Workshop).filter_by(name=workshop_name).first()
                
                if workshop:
                    self._add_result(True, f"Цех '{workshop_name}' найден в БД")
                else:
                    self._add_result(False, f"Цех '{workshop_name}' не найден в БД")
                    
        except Exception as e:
            self._add_result(False, f"Ошибка проверки цехов: {e}")
    
    def check_products(self):
        """Проверка продукции"""
        logger.info("\n🔍 Проверка продукции...")
        
        try:
            excel_file = EXCEL_FILES['products']
            df = pd.read_excel(excel_file)
            df.columns = df.columns.str.strip()
            
            excel_count = len(df)
            db_count = self.session.query(Product).count()
            
            self._add_result(
                excel_count == db_count,
                f"Продукция: совпадение количества (Excel: {excel_count}, БД: {db_count})"
            )
            
            # Проверяем ссылочную целостность
            # Продукты без типа
            products_without_type = self.session.query(Product).filter(
                ~Product.product_type_id.in_(self.session.query(ProductType.id))
            ).count()
            
            # Продукты без материала
            products_without_material = self.session.query(Product).filter(
                ~Product.material_id.in_(self.session.query(MaterialType.id))
            ).count()
            
            self._add_result(
                products_without_type == 0 and products_without_material == 0,
                f"Ссылочная целостность продуктов: "
                f"без типа - {products_without_type}, без материала - {products_without_material}"
            )
            
            # Проверяем несколько продуктов
            sample_size = min(3, len(df))
            for i in range(sample_size):
                row = df.iloc[i]
                product_name = str(row['Наименование продукции']).strip()
                
                product = self.session.query(Product).filter_by(name=product_name).first()
                
                if product:
                    self._add_result(True, f"Продукт '{product_name}' найден в БД")
                else:
                    self._add_result(False, f"Продукт '{product_name}' не найден в БД")
                    
        except Exception as e:
            self._add_result(False, f"Ошибка проверки продукции: {e}")
    
    def check_product_workshop_links(self):
        """Проверка связей продукции и цехов"""
        logger.info("\n🔍 Проверка связей продукции и цехов...")
        
        try:
            excel_file = EXCEL_FILES['product_workshop']
            df = pd.read_excel(excel_file)
            df.columns = df.columns.str.strip()
            
            excel_count = len(df)
            
            # Получаем количество связей из БД
            from sqlalchemy import select as sql_select
            link_count = self.session.execute(
                sql_select(func.count()).select_from(product_workshop_table)
            ).scalar() or 0
            
            self._add_result(
                excel_count == link_count,
                f"Связи продукция-цеха: совпадение количества (Excel: {excel_count}, БД: {link_count})"
            )
            
            # Проверяем "битые" ссылки (SQLAlchemy способ)
            # Считаем связи, где product_id не существует в products
            broken_product_links = self.session.execute(
                sql_select(func.count())
                .select_from(product_workshop_table)
                .where(~exists().where(Product.id == product_workshop_table.c.product_id))
            ).scalar() or 0
            
            # Считаем связи, где workshop_id не существует в workshops
            broken_workshop_links = self.session.execute(
                sql_select(func.count())
                .select_from(product_workshop_table)
                .where(~exists().where(Workshop.id == product_workshop_table.c.workshop_id))
            ).scalar() or 0
            
            total_broken = broken_product_links + broken_workshop_links
            
            self._add_result(
                total_broken == 0,
                f"Целостность связей: найдено {total_broken} битых ссылок "
                f"(продукты: {broken_product_links}, цеха: {broken_workshop_links})"
            )
            
        except Exception as e:
            self._add_result(False, f"Ошибка проверки связей: {e}")
    
    def check_data_integrity(self):
        """Проверка целостности данных"""
        logger.info("\n🔍 Проверка целостности данных...")
        
        try:
            # 1. Проверка уникальности артикулов
            duplicate_articles = self.session.execute(
                select(Product.article, func.count(Product.article))
                .group_by(Product.article)
                .having(func.count(Product.article) > 1)
            ).fetchall()
            
            self._add_result(
                len(duplicate_articles) == 0,
                f"Уникальность артикулов: найдено {len(duplicate_articles)} дубликатов"
            )
            
            # 2. Проверка отрицательных цен
            negative_prices = self.session.query(Product).filter(
                Product.min_partner_price < 0
            ).count()
            
            self._add_result(
                negative_prices == 0,
                f"Отрицательные цены: найдено {negative_prices} записей"
            )
            
            # 3. Проверка отрицательного времени производства
            negative_time = self.session.execute(
                select(func.count())
                .select_from(product_workshop_table)
                .where(product_workshop_table.c.manufacturing_time_hours < 0)
            ).scalar() or 0
            
            self._add_result(
                negative_time == 0,
                f"Отрицательное время производства: найдено {negative_time} записей"
            )
            
            # 4. Проверка продуктов без цехов
            products_without_workshops = self.session.query(Product).filter(
                ~exists().where(product_workshop_table.c.product_id == Product.id)
            ).count()
            
            self._add_result(
                products_without_workshops == 0,
                f"Продукты без цехов: найдено {products_without_workshops} записей"
            )
            
            # 5. Проверка цехов без продуктов
            workshops_without_products = self.session.query(Workshop).filter(
                ~exists().where(product_workshop_table.c.workshop_id == Workshop.id)
            ).count()
            
            self._add_result(
                workshops_without_products == 0,
                f"Цеха без продуктов: найдено {workshops_without_products} записей"
            )
            
        except Exception as e:
            self._add_result(False, f"Ошибка проверки целостности: {e}")
    
    def run_all_checks(self):
        """Запуск всех проверок"""
        print("=" * 70)
        print("ПРОВЕРКА КОРРЕКТНОСТИ ИМПОРТА ДАННЫХ")
        print("=" * 70)
        
        try:
            self.session = get_session()
            
            # Выполняем все проверки
            self.check_material_types()
            self.check_product_types()
            self.check_workshops()
            self.check_products()
            self.check_product_workshop_links()
            self.check_data_integrity()
            
            # Выводим итоговый отчет
            self.print_summary()
            
        except Exception as e:
            print(f"\n❌ Критическая ошибка при проверке: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.session:
                self.session.close()
    
    def print_summary(self):
        """Вывод итогового отчета"""
        print("\n" + "=" * 70)
        print("ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 70)
        
        # Статистика
        print(f"\n📊 Статистика проверок:")
        print(f"   Всего проверок: {self.results['total_checks']}")
        print(f"   Успешно:        {self.results['passed_checks']}")
        print(f"   Провалено:      {self.results['failed_checks']}")
        
        # Процент успеха
        if self.results['total_checks'] > 0:
            success_rate = (self.results['passed_checks'] / self.results['total_checks']) * 100
            print(f"   Успешность:     {success_rate:.1f}%")
        
        # Общий вердикт
        print(f"\n🎯 Результат: ", end="")
        if self.results['failed_checks'] == 0:
            print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print(f"⚠ НАЙДЕНЫ ПРОБЛЕМЫ: {self.results['failed_checks']} ошибок")
        
        # Детали проверок (показываем все)
        print(f"\n🔎 Детали проверок:")
        for detail in self.results['details']:
            print(f"   {detail}")
        
        # Рекомендации
        print(f"\n💡 Рекомендации:")
        if self.results['failed_checks'] == 0:
            print("   1. ✅ Импорт выполнен корректно")
            print("   2. ✅ Данные готовы к использованию")
            print("   3. ✅ Можете приступать к следующему заданию")
        else:
            print("   1. ⚠ Проверьте исходные Excel файлы")
            print("   2. ⚠ Убедитесь в правильности названий столбцов")
            print("   3. ⚠ Перезапустите импорт: python -m app.scripts.import_data")
            print("   4. ⚠ После исправлений снова запустите проверку")
        
        print("\n" + "=" * 70)

def main():
    """Точка входа"""
    validator = ImportValidator()
    validator.run_all_checks()

if __name__ == "__main__":
    main()