import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Dev routes are gated by ENABLE_DEV_ROUTES (default off for security).
# Set to enable /dev/* endpoints in smoke test.
os.environ.setdefault("ENABLE_DEV_ROUTES", "1")

from backend.configs.realms import REALM_NAMES  # noqa: E402


BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
DB_PATH = Path(os.environ.get("DB_PATH", ROOT / "game.db"))
RAW_CODE_RE = re.compile(r"\b[a-z]+(?:_[a-z0-9]+)+\b")


def request(path, method="GET", token=None, payload=None):
    body = json.dumps(payload or {}).encode("utf-8") if method != "GET" else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8")
        raise RuntimeError(f"{method} {path} failed: {error.code} {detail}") from error


def action(token, action_type, params=None):
    return request("/action/execute", "POST", token=token, payload={"action_type": action_type, "params": params or {}})


def assert_no_raw_code(text):
    assert not RAW_CODE_RE.search(text or ""), text


def assert_visible_chinese(text):
    assert text and not RAW_CODE_RE.search(text), text


def register_user():
    username = f"locqa_{int(time.time() * 1000)}"
    token = request("/register", "POST", payload={"username": username, "password": "123456"})["token"]
    return username, token


def get_ids(username):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT users.id, characters.id
            FROM users
            JOIN characters ON characters.user_id = users.id
            WHERE users.username = ?
            """,
            (username,),
        ).fetchone()
    assert row, username
    return row[0], row[1]


def force_character(username, **fields):
    _user_id, character_id = get_ids(username)
    assignments = ", ".join(f"{name} = ?" for name in fields)
    values = list(fields.values()) + [character_id]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"UPDATE characters SET {assignments} WHERE id = ?", values)
        conn.commit()


def add_item_to_bag(username, code, quantity=1, rarity="凡品"):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        template = conn.execute("SELECT id, stackable FROM item_templates WHERE code = ?", (code,)).fetchone()
        assert template, code
        template_id, stackable = template
        if stackable:
            slot = conn.execute(
                """
                SELECT id, quantity FROM inventory_slots
                WHERE character_id = ? AND container_type = 'main_bag' AND container_id = 0 AND item_template_id = ?
                ORDER BY slot_index
                LIMIT 1
                """,
                (character_id, template_id),
            ).fetchone()
            if slot:
                conn.execute("UPDATE inventory_slots SET quantity = ? WHERE id = ?", (slot[1] + quantity, slot[0]))
                conn.commit()
                return
        slot_id = conn.execute(
            """
            SELECT id FROM inventory_slots
            WHERE character_id = ? AND container_type = 'main_bag' AND container_id = 0 AND item_template_id IS NULL
            ORDER BY slot_index
            LIMIT 1
            """,
            (character_id,),
        ).fetchone()[0]
        item_instance_id = None
        if not stackable:
            conn.execute(
                """
                INSERT INTO item_instances (item_template_id, owner_character_id, durability, level, exp, rarity, bound, extra_json)
                VALUES (?, ?, 100, 1, 0, ?, 0, '{}')
                """,
                (template_id, character_id, rarity),
            )
            item_instance_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            quantity = 1
        conn.execute(
            """
            UPDATE inventory_slots
            SET item_template_id = ?, quantity = ?, item_instance_id = ?
            WHERE id = ?
            """,
            (template_id, quantity, item_instance_id, slot_id),
        )
        conn.commit()


def first_slot_with_code(username, code):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT inventory_slots.slot_index
            FROM inventory_slots
            JOIN item_templates ON item_templates.id = inventory_slots.item_template_id
            WHERE inventory_slots.character_id = ? AND item_templates.code = ?
            ORDER BY inventory_slots.slot_index
            LIMIT 1
            """,
            (character_id, code),
        ).fetchone()
    assert row, code
    return row[0]


def check_recipes_are_localized():
    recipes = request("/life-skills/recipes")
    expected_counts = {"alchemy": 6, "talisman": 6, "crafting": 6, "formation": 3}
    for skill_type, minimum in expected_counts.items():
        assert len(recipes[skill_type]) >= minimum, (skill_type, len(recipes[skill_type]))
        for recipe in recipes[skill_type]:
            assert_visible_chinese(recipe["name"])
            output_name = recipe.get("output_item_name") or recipe.get("output_effect_name") or recipe.get("output_name")
            assert_visible_chinese(output_name)
            assert "materials" in recipe and recipe["materials"], recipe
            for material in recipe["materials"]:
                assert_visible_chinese(material["name"])
    return recipes


def main():
    request("/dev/health")
    recipes = check_recipes_are_localized()

    username, token = register_user()

    missing = action(token, "alchemy", {"recipe_id": "alchemy_huichun_pill"})
    assert missing["success"] is False
    assert "缺少材料" in missing["message"], missing["message"]
    assert "疗伤草" in missing["message"], missing["message"]
    assert_no_raw_code(missing["message"])

    force_character(
        username,
        realm=REALM_NAMES[4],
        realm_stage="炼气",
        mana=1000,
        max_mana=1000,
        spirit_stones=500,
        cultivation=0,
    )
    joined = action(token, "join_sect", {"sect_code": "qingxuan_sword_sect"})
    assert joined["success"] is True, joined["message"]
    with sqlite3.connect(DB_PATH) as conn:
        _uid, character_id = get_ids(username)
        conn.execute("UPDATE sect_members SET contribution = 500 WHERE character_id = ?", (character_id,))
        conn.commit()

    shop = request("/sects/shop", token=token)
    assert shop, "sect shop should not be empty"
    for item in shop:
        assert_visible_chinese(item["name"])
        assert_visible_chinese(item["item_name"])
        assert "获得" in item["exchange_summary"]
        assert_no_raw_code(item["exchange_summary"])

    for code, quantity in {"healing_herb": 10, "low_spirit_stone": 100, "low_material": 40}.items():
        add_item_to_bag(username, code, quantity)

    craft_plan = [
        ("alchemy", "alchemy_huichun_pill", "回春丹"),
        ("talisman", "talisman_explore_luck", "探路符"),
        ("crafting", "craft_qingmu_pendant", "青木佩"),
        ("formation", "formation_gather_spirit", "聚灵阵"),
    ]
    for skill_type, recipe_id, visible_name in craft_plan:
        result = action(token, skill_type, {"recipe_id": recipe_id})
        assert result["success"] is True, result["message"]
        assert visible_name in result["message"], result["message"]
        assert_no_raw_code(result["message"])

    bag = request("/inventory", token=token)
    bag_names = {slot["name"] for slot in bag if slot.get("name")}
    for expected in ["回春丹", "探路符", "青木佩"]:
        assert expected in bag_names, (expected, bag_names)
    for name in bag_names:
        assert_visible_chinese(name)

    slot_index = first_slot_with_code(username, "qingmu_pendant")
    equipped = action(token, "equip_artifact", {"slot_index": slot_index})
    assert equipped["success"] is True, equipped["message"]
    assert "青木佩" in equipped["message"], equipped["message"]
    assert_no_raw_code(equipped["message"])

    assert recipes["alchemy"][0]["output_item_name"]
    print("Localization player flow test passed.")


if __name__ == "__main__":
    main()
