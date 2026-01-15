"""Проверка применения миграций"""
from sqlalchemy import create_engine, text
from app.config import settings

DATABASE_URL = f"postgresql://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

try:
    with engine.connect() as conn:
        # Проверяем наличие таблиц
        tables_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'mnt' 
            AND table_name IN ('document_versions', 'tags', 'document_tags')
            ORDER BY table_name
        """)
        
        result = conn.execute(tables_query)
        tables = [row[0] for row in result]
        
        print("[INFO] Проверка примененных миграций:")
        print()
        
        expected_tables = ['document_versions', 'document_tags', 'tags']
        all_exist = True
        
        for table in expected_tables:
            if table in tables:
                print(f"[OK] Таблица mnt.{table} существует")
            else:
                print(f"[ERROR] Таблица mnt.{table} НЕ найдена")
                all_exist = False
        
        if all_exist:
            print()
            print("[SUCCESS] Все миграции применены успешно!")
        else:
            print()
            print("[ERROR] Некоторые таблицы отсутствуют")
            
except Exception as e:
    print(f"[ERROR] Ошибка при проверке: {e}")
