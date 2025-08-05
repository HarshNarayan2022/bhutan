from sqlalchemy import text
from backend.scripts.db.session import engine

def create_vector_extension():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;"))
        print("[INFO] 'vector' extension created if not present.")

if __name__ == "__main__":
    create_vector_extension()