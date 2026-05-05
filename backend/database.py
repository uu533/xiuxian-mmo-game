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
    migrate_realms()


def ensure_character_columns() -> None:
    columns = {
        "title": "VARCHAR(24) NOT NULL DEFAULT '师兄'",
        "sect_name": "VARCHAR(64)",
        "sect_branch": "VARCHAR(64)",
        "cultivation_method_attack_bonus": "INTEGER NOT NULL DEFAULT 0",
        "cultivation_method_defense_bonus": "INTEGER NOT NULL DEFAULT 0",
        "cultivation_method_mana_bonus": "INTEGER NOT NULL DEFAULT 0",
        "magic_treasure_attack_bonus": "INTEGER NOT NULL DEFAULT 0",
        "magic_treasure_defense_bonus": "INTEGER NOT NULL DEFAULT 0",
        "magic_treasure_mana_bonus": "INTEGER NOT NULL DEFAULT 0",
    }
    with engine.begin() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(characters)")).fetchall()}
        for name, definition in columns.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE characters ADD COLUMN {name} {definition}"))
    drop_deprecated_action_columns()


def drop_deprecated_action_columns() -> None:
    deprecated = [
        "action_points",
        "max_action_points",
        "action_spent_total",
        "age_progress",
        "last_action_recovered_at",
        "attack",
        "defense",
    ]
    with engine.begin() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(characters)")).fetchall()}
        for name in deprecated:
            if name in existing:
                try:
                    conn.execute(text(f"ALTER TABLE characters DROP COLUMN {name}"))
                except Exception:
                    # Older SQLite builds may not support DROP COLUMN. The ORM no longer reads these fields.
                    pass


def migrate_realms() -> None:
    with engine.begin() as conn:
        conn.execute(text("UPDATE characters SET realm = '炼气一层', cultivation_cap = MAX(cultivation_cap, 80) WHERE realm = '炼气'"))
        conn.execute(text("UPDATE characters SET realm = '筑基初期', cultivation_cap = MAX(cultivation_cap, 4200) WHERE realm = '筑基'"))
        conn.execute(text("UPDATE characters SET realm = '结丹初期', cultivation_cap = MAX(cultivation_cap, 17000) WHERE realm IN ('金丹', '结丹')"))
        conn.execute(text("UPDATE characters SET realm = '元婴初期', cultivation_cap = MAX(cultivation_cap, 92000) WHERE realm = '元婴'"))
        conn.execute(text("UPDATE characters SET realm = '化神初期', cultivation_cap = MAX(cultivation_cap, 520000) WHERE realm = '化神'"))
