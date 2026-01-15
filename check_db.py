"""Скрипт для просмотра данных из БД"""
from app.database import SessionLocal
from sqlalchemy import text

def view_all_documents():
    """Просмотр всех записей МНТ"""
    db = SessionLocal()
    try:
        query = text("""
            SELECT id, title, project, author, status, 
                   confluence_space, confluence_page_id, confluence_page_url,
                   last_error, created_at, updated_at
            FROM mnt.documents
            ORDER BY created_at DESC
        """)
        
        result = db.execute(query)
        rows = result.fetchall()
        
        print("=" * 80)
        print("Все записи МНТ в базе данных:")
        print("=" * 80)
        
        if not rows:
            print("Записей не найдено")
            return
        
        for row in rows:
            print(f"\nID: {row[0]}")
            print(f"Название: {row[1]}")
            print(f"Проект: {row[2]}")
            print(f"Автор: {row[3]}")
            print(f"Статус: {row[4]}")
            print(f"Confluence Space: {row[5]}")
            print(f"Confluence Page ID: {row[6]}")
            print(f"Confluence URL: {row[7]}")
            print(f"Ошибка (last_error): {row[8] if row[8] else '(нет ошибки)'}")
            print(f"Создано: {row[9]}")
            print(f"Обновлено: {row[10]}")
            print("-" * 80)
    
    finally:
        db.close()


def view_data_json(id_val):
    """Просмотр data_json для конкретной записи"""
    db = SessionLocal()
    try:
        query = text("""
            SELECT data_json
            FROM mnt.documents
            WHERE id = :id
        """)
        
        result = db.execute(query, {"id": id_val})
        row = result.fetchone()
        
        if row:
            import json
            data = row[0]
            if isinstance(data, str):
                data = json.loads(data)
            print(f"\nДанные формы (data_json) для ID {id_val}:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"Запись с ID {id_val} не найдена")
    
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Просмотр data_json для конкретного ID
        try:
            doc_id = int(sys.argv[1])
            view_data_json(doc_id)
        except ValueError:
            print("Использование: python check_db.py [id]")
    else:
        # Просмотр всех записей
        view_all_documents()
