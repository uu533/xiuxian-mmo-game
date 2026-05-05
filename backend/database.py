from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'game.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    from backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_character_columns()


def ensure_character_columns() -> None:
    columns = {
        "action_points": "INTEGER NOT NULL DEFAULT 100",
        "max_action_points": "INTEGER NOT NULL DEFAULT 100",
        "action_spent_total": "INTEGER NOT NULL DEFAULT 0",
        "age_progress": "INTEGER NOT NULL DEFAULT 0",
        "last_action_recovered_at": "DATETIME",
    }
    with engine.begin() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(characters)")).fetchall()}
        for name, definition in columns.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE characters ADD COLUMN {name} {definition}"))
        conn.execute(
            text(
                """
                UPDATE characters
                SET last_action_recovered_at = COALESCE(last_action_recovered_at, CURRENT_TIMESTAMP)
                """
            )
        )
