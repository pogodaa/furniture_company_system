from app.database.database import get_session

def get_db():
    """Простой генератор сессий"""
    db = get_session()
    try:
        yield db
    finally:
        db.close()