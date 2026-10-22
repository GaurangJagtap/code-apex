from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)
    try:
        inspector = inspect(engine)
        if "bug_findings" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("bug_findings")]
            if "dedup_key" not in columns:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE bug_findings ADD COLUMN dedup_key VARCHAR"))
    except Exception as e:
        print(f"DB init migration notice: {e}")

init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
