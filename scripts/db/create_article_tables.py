from backend.scripts.migration_schemas.resources_models import Base
from backend.scripts.db.session import engine
from sqlalchemy import inspect

def create_tables():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    Base.metadata.create_all(bind=engine)

    updated_tables = inspector.get_table_names()
    new_tables = set(updated_tables) - set(existing_tables)

    if new_tables:
        print(f"[INFO] Created new article tables: {', '.join(new_tables)}")
    else:
        print("[INFO] No new article tables created. All tables already exist.")

if __name__ == "__main__":
    create_tables()