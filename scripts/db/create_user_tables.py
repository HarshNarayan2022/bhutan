from backend.scripts.migration_schemas.user_models import Base
from backend.scripts.db.session import engine
from sqlalchemy import inspect

def create_tables():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # This will create all tables defined on Base.metadata that don't yet exist
    Base.metadata.create_all(bind=engine)

    updated_tables = inspector.get_table_names()
    new_tables = set(updated_tables) - set(existing_tables)

    if new_tables:
        print(f"[INFO] Created new tables: {', '.join(new_tables)}")
    else:
        print("[INFO] No new tables created. All tables already exist.")

if __name__ == "__main__":
    create_tables()