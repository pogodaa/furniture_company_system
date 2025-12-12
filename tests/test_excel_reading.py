import pandas as pd
from pathlib import Path

file_path = Path("data/isxod/Material_type_import.xlsx")
df = pd.read_excel(file_path)

print("=== ЧТЕНИЕ EXCEL ===")
print(f"Файл: {file_path}")
print(f"Колонки: {df.columns.tolist()}")
print("\nДанные:")
for idx, row in df.iterrows():
    value = row['Процент потерь сырья']
    print(f"  Строка {idx + 2}: '{value}' (тип: {type(value).__name__})")
    
print("\nИнформация о датафрейме:")
print(df.info())