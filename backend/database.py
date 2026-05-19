from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'game.db'}"
DB_REBUILD_HINT = "旧数据库结构不兼容时，可停止服务后删除项目根目录 game.db，再重新启动自动建表并重新注册测试账号。"

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
    migrate_early_mvp_schema()
    migrate_auto_cultivation_schema()
    seed_item_templates()
    seed_default_sects()
    ensure_existing_character_runtime_data()


def migrate_early_mvp_schema() -> None:
    with engine.begin() as conn:
        _add_missing_columns(
            conn,
            "users",
            {
                "last_login_at": "DATETIME",
                "status": "VARCHAR(24) NOT NULL DEFAULT 'active'",
            },
        )
        _add_missing_columns(
            conn,
            "characters",
            {
                "name": "VARCHAR(32) NOT NULL DEFAULT ''",
                "realm_stage": "VARCHAR(16) NOT NULL DEFAULT '炼气'",
                "max_hp": "INTEGER NOT NULL DEFAULT 100",
                "max_mana": "INTEGER NOT NULL DEFAULT 100",
                "base_attack": "INTEGER NOT NULL DEFAULT 5",
                "base_defense": "INTEGER NOT NULL DEFAULT 5",
                "hidden_luck": "INTEGER NOT NULL DEFAULT 50",
                "hidden_inner_demon": "INTEGER NOT NULL DEFAULT 0",
                "scout_talisman_charges": "INTEGER NOT NULL DEFAULT 0",
                "guard_talisman_charges": "INTEGER NOT NULL DEFAULT 0",
                "swift_talisman_charges": "INTEGER NOT NULL DEFAULT 0",
                "sect_id": "INTEGER",
                "sect_position": "VARCHAR(32) NOT NULL DEFAULT '散修'",
                "created_at": "DATETIME",
            },
        )
        _add_missing_columns(
            conn,
            "item_instances",
            {
                "rarity": "VARCHAR(8) NOT NULL DEFAULT '白'",
            },
        )
        _add_missing_columns(
            conn,
            "sects",
            {
                "code": "VARCHAR(64)",
                "faction": "VARCHAR(24) NOT NULL DEFAULT 'righteous'",
                "is_player_created": "INTEGER NOT NULL DEFAULT 0",
                "leader_character_id": "INTEGER",
                "updated_at": "DATETIME",
            },
        )
        _add_missing_columns(
            conn,
            "sect_members",
            {
                "reputation": "INTEGER NOT NULL DEFAULT 0",
                "last_task_at": "DATETIME",
                "last_left_at": "DATETIME",
                "status": "VARCHAR(24) NOT NULL DEFAULT 'active'",
            },
        )
        if "code" in _columns(conn, "sects"):
            conn.execute(text("UPDATE sects SET code = COALESCE(NULLIF(code, ''), 'legacy_' || id)"))
        if "updated_at" in _columns(conn, "sects"):
            conn.execute(text("UPDATE sects SET updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)"))
        existing = _columns(conn, "characters")
        if "luck" in existing:
            conn.execute(text("UPDATE characters SET hidden_luck = COALESCE(luck, hidden_luck)"))
        if "inner_demon" in existing:
            conn.execute(text("UPDATE characters SET hidden_inner_demon = COALESCE(inner_demon, hidden_inner_demon)"))
        conn.execute(text("UPDATE characters SET name = COALESCE(NULLIF(name, ''), (SELECT username FROM users WHERE users.id = characters.user_id), '道友')"))
        conn.execute(text("UPDATE characters SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)"))
        conn.execute(text("UPDATE characters SET realm = '炼气一层', realm_stage = '炼气', cultivation_cap = MAX(cultivation_cap, 80) WHERE realm = '炼气'"))
        conn.execute(text("UPDATE characters SET realm = '筑基初期', realm_stage = '筑基', cultivation_cap = MAX(cultivation_cap, 4200) WHERE realm = '筑基'"))
        conn.execute(text("UPDATE characters SET realm = '结丹初期', realm_stage = '结丹', cultivation_cap = MAX(cultivation_cap, 17000) WHERE realm IN ('金丹', '结丹')"))
        conn.execute(text("UPDATE characters SET realm = '元婴初期', realm_stage = '元婴', cultivation_cap = MAX(cultivation_cap, 92000) WHERE realm = '元婴'"))
        conn.execute(text("UPDATE characters SET realm = '化神初期', realm_stage = '化神', cultivation_cap = MAX(cultivation_cap, 520000) WHERE realm = '化神'"))
        _drop_columns_if_possible(
            conn,
            "characters",
            [
                "action_points",
                "max_action_points",
                "action_spent_total",
                "age_progress",
                "last_action_recovered_at",
                "luck",
                "inner_demon",
                "attack",
                "defense",
                "cultivation_method_attack_bonus",
                "cultivation_method_defense_bonus",
                "cultivation_method_mana_bonus",
                "magic_treasure_attack_bonus",
                "magic_treasure_defense_bonus",
                "magic_treasure_mana_bonus",
            ],
        )


def migrate_auto_cultivation_schema() -> None:
    with engine.begin() as conn:
        _add_missing_columns(
            conn,
            "characters",
            {
                "auto_enabled": "INTEGER NOT NULL DEFAULT 0",
                "auto_strategy": "VARCHAR(24) NOT NULL DEFAULT 'balanced'",
                "auto_state": "VARCHAR(24) NOT NULL DEFAULT 'meditating'",
                "last_auto_settle_at": "DATETIME",
                "last_auto_report_json": "TEXT",
                "last_auto_log_json": "TEXT",
                "auto_paused_reason": "VARCHAR(128)",
            },
        )


def seed_item_templates() -> None:
    from backend.configs.items import ITEM_TEMPLATES

    with engine.begin() as conn:
        for item in ITEM_TEMPLATES:
            exists = conn.execute(text("SELECT id FROM item_templates WHERE code = :code"), {"code": item["code"]}).fetchone()
            payload = {
                "code": item["code"],
                "name": item["name"],
                "type": item["type"],
                "grade": item["grade"],
                "description": item["description"],
                "stackable": 1 if item["stackable"] else 0,
                "max_stack": item["max_stack"],
                "effects_json": _json_dumps(item["effects"]),
            }
            if exists:
                conn.execute(
                    text(
                        """
                        UPDATE item_templates
                        SET name = :name, type = :type, grade = :grade, description = :description,
                            stackable = :stackable, max_stack = :max_stack, effects_json = :effects_json
                        WHERE code = :code
                        """
                    ),
                    payload,
                )
            else:
                conn.execute(
                    text(
                        """
                        INSERT INTO item_templates (code, name, type, grade, description, stackable, max_stack, effects_json)
                        VALUES (:code, :name, :type, :grade, :description, :stackable, :max_stack, :effects_json)
                        """
                    ),
                    payload,
                )


def seed_default_sects() -> None:
    from backend.configs.sects import NPC_SECTS

    with engine.begin() as conn:
        for sect in NPC_SECTS:
            exists = conn.execute(text("SELECT id FROM sects WHERE code = :code"), {"code": sect["code"]}).fetchone()
            payload = {
                "code": sect["code"],
                "name": sect["name"],
                "faction": sect["faction"],
                "level": sect["level"],
                "description": sect["description"],
            }
            if exists:
                conn.execute(
                    text(
                        """
                        UPDATE sects
                        SET name = :name, faction = :faction, level = :level,
                            description = :description, is_player_created = 0,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE code = :code
                        """
                    ),
                    payload,
                )
            else:
                conn.execute(
                    text(
                        """
                        INSERT INTO sects
                            (code, name, faction, level, description, is_player_created, created_at, updated_at)
                        VALUES
                            (:code, :name, :faction, :level, :description, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """
                    ),
                    payload,
                )


def ensure_existing_character_runtime_data() -> None:
    from backend.models import Character
    from backend.services.calc_service import sync_base_and_caps
    from backend.services.inventory_service import ensure_main_bag_slots
    from backend.services.realm_service import normalize_realm
    from backend.services.task_service import ensure_character_tasks

    db = SessionLocal()
    try:
        for character in db.query(Character).all():
            normalize_realm(character)
            sync_base_and_caps(character)
            ensure_main_bag_slots(db, character)
            ensure_character_tasks(db, character)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise RuntimeError(f"数据库迁移失败。{DB_REBUILD_HINT}") from exc
    finally:
        db.close()


def db_summary() -> dict:
    with engine.connect() as conn:
        tables = [row[0] for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).fetchall()]
        return {
            "database": str(BASE_DIR / "game.db"),
            "tables": tables,
            "users": _count(conn, "users"),
            "characters": _count(conn, "characters"),
            "inventory_slots": _count(conn, "inventory_slots"),
            "item_templates": _count(conn, "item_templates"),
            "character_tasks": _count(conn, "character_tasks"),
            "game_logs": _count(conn, "game_logs"),
            "action_records": _count(conn, "action_records"),
            "active_effects": _count(conn, "active_effects"),
            "life_skill_records": _count(conn, "life_skill_records"),
            "sects": _count(conn, "sects"),
            "sect_members": _count(conn, "sect_members"),
            "sect_tasks": _count(conn, "sect_tasks"),
            "rebuild_hint": DB_REBUILD_HINT,
        }


def _columns(conn, table: str) -> set[str]:
    return {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()}


def _add_missing_columns(conn, table: str, definitions: dict[str, str]) -> None:
    existing = _columns(conn, table)
    for name, definition in definitions.items():
        if name not in existing:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))


def _drop_columns_if_possible(conn, table: str, columns: list[str]) -> None:
    existing = _columns(conn, table)
    for name in columns:
        if name in existing:
            try:
                conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {name}"))
            except Exception:
                pass


def _count(conn, table: str) -> int:
    try:
        return int(conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one())
    except Exception:
        return 0


def _json_dumps(value: dict) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)
