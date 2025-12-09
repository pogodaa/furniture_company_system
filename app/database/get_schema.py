
from pathlib import Path
import sqlite3

# Путь к вашей базе
DB_PATH = Path(__file__).parent.parent / "database" / "furniture.db"

def get_exact_schema():
    """Получает точную схему из вашей базы данных"""
    
    if not DB_PATH.exists():
        print(f"❌ База данных не найдена: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("РЕАЛЬНАЯ СХЕМА ВАШЕЙ БАЗЫ ДАННЫХ")
    print("=" * 70)
    
    # 1. Получаем все таблицы
    cursor.execute("""
        SELECT name, sql 
        FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    
    tables = cursor.fetchall()
    
    all_sql = []
    
    for table_name, table_sql in tables:
        print(f"\n📋 ТАБЛИЦА: {table_name}")
        print("-" * 50)
        
        if table_sql:
            print(table_sql)
            all_sql.append(table_sql)
            
            # Получаем дополнительную информацию
            print(f"\n🔍 СТРУКТУРА {table_name}:")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_id, col_name, col_type, not_null, default, pk = col
                flags = []
                if pk: flags.append("PRIMARY KEY")
                if not_null: flags.append("NOT NULL")
                if default: flags.append(f"DEFAULT {default}")
                
                flags_str = " ".join(flags)
                print(f"  - {col_name}: {col_type} {flags_str}")
            
            # Внешние ключи (исправленная версия)
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            fks = cursor.fetchall()
            
            if fks:
                print(f"\n🔗 ВНЕШНИЕ КЛЮЧИ {table_name}:")
                for fk in fks:
                    # Разные версии SQLite возвращают разное количество полей
                    if len(fk) >= 4:
                        id_, seq, table_to, col_from, col_to, on_update, on_delete, match = fk[:8]
                        print(f"  - {col_from} → {table_to}.{col_to}")
        
        print("-" * 50)
    
    conn.close()
    
    # Сохраняем полный SQL В ТЕКУЩУЮ ПАПКУ database
    output_dir = DB_PATH.parent  # Папка, где находится furniture.db
    
    full_sql = "\n".join(all_sql)
    
    # Сохраняем в тот же каталог, где база данных
    sql_file_path = output_dir / "db_schema.sql"
    with open(sql_file_path, "w", encoding="utf-8") as f:
        f.write(full_sql)
    
    print(f"\n✅ Полный SQL сохранен в: {sql_file_path}")
    print(f"📁 Рядом с файлом базы данных: {DB_PATH}")
    
    
if __name__ == "__main__":
    get_exact_schema()






