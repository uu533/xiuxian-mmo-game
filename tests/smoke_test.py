import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.configs.realms import REALM_NAMES

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "game.db"
SIMULATION_PATH = ROOT / "simulation_result.json"
HIDDEN_FIELDS = {"hidden_luck", "hidden_inner_demon", "luck", "inner_demon", "action_points"}


def request(path, method="GET", token=None, payload=None):
    body = json.dumps(payload or {}).encode("utf-8") if method != "GET" else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8")
        raise RuntimeError(f"{method} {path} failed: {error.code} {detail}") from error


def register(username):
    return request("/register", "POST", payload={"username": username, "password": "123456"})


def login(username):
    return request("/login", "POST", payload={"username": username, "password": "123456"})["token"]


def action(token, action_type, params=None):
    return request("/action/execute", "POST", token=token, payload={"action_type": action_type, "params": params or {}})


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
    return row[0], row[1]


def force_character(username, **fields):
    _user_id, character_id = get_ids(username)
    assignments = ", ".join(f"{name} = ?" for name in fields)
    values = list(fields.values()) + [character_id]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"UPDATE characters SET {assignments} WHERE id = ?", values)
        conn.commit()


def add_item_to_bag(username, code, quantity=1, rarity="白"):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        template = conn.execute("SELECT id, stackable FROM item_templates WHERE code = ?", (code,)).fetchone()
        template_id, stackable = template
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
        slot_index = conn.execute("SELECT slot_index FROM inventory_slots WHERE id = ?", (slot_id,)).fetchone()[0]
        conn.commit()
    return slot_index


def remove_item_from_bag(username, code):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        template = conn.execute("SELECT id FROM item_templates WHERE code = ?", (code,)).fetchone()
        if not template:
            return
        conn.execute(
            """
            UPDATE inventory_slots
            SET item_template_id = NULL, quantity = 0, item_instance_id = NULL
            WHERE character_id = ? AND item_template_id = ?
            """,
            (character_id, template[0]),
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
    return row[0] if row else None


def add_explore_records(username, count):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        for _ in range(count):
            conn.execute(
                """
                INSERT INTO action_records (character_id, action_type, cost_json, result_json, created_at)
                VALUES (?, 'explore', '{}', '{"success": true}', CURRENT_TIMESTAMP)
                """,
                (character_id,),
            )
        conn.commit()


def recent_action_results(username, action_type, limit):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT result_json FROM action_records
            WHERE character_id = ? AND action_type = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (character_id, action_type, limit),
        ).fetchall()
    return [json.loads(row[0]) if isinstance(row[0], str) else row[0] for row in reversed(rows)]


def set_first_method_to_level(username, level, exp=0):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE character_methods SET level = ?, exp = ?, equipped = 1 WHERE character_id = ?", (level, exp, character_id))
        conn.commit()


def set_first_artifact_rarity(username, rarity="白"):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE item_instances
            SET rarity = ?
            WHERE id = (
                SELECT item_instance_id FROM character_artifacts
                WHERE character_id = ?
                ORDER BY id
                LIMIT 1
            )
            """,
            (rarity, character_id),
        )
        conn.commit()


def force_active_sect_member(username, **fields):
    _user_id, character_id = get_ids(username)
    assignments = ", ".join(f"{name} = ?" for name in fields)
    values = list(fields.values()) + [character_id]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"UPDATE sect_members SET {assignments} WHERE character_id = ? AND status = 'active'", values)
        conn.commit()


def fill_inventory(username):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        template_id = conn.execute("SELECT id FROM item_templates WHERE code = 'low_artifact'").fetchone()[0]
        empty_slots = conn.execute(
            """
            SELECT id FROM inventory_slots
            WHERE character_id = ? AND container_type = 'main_bag' AND container_id = 0 AND item_template_id IS NULL
            """,
            (character_id,),
        ).fetchall()
        for (slot_id,) in empty_slots:
            conn.execute(
                """
                INSERT INTO item_instances (item_template_id, owner_character_id, durability, level, exp, rarity, bound, extra_json)
                VALUES (?, ?, 100, 1, 0, '白', 0, '{}')
                """,
                (template_id, character_id),
            )
            instance_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                """
                UPDATE inventory_slots
                SET item_template_id = ?, quantity = 1, item_instance_id = ?
                WHERE id = ?
                """,
                (template_id, instance_id, slot_id),
            )
        conn.commit()


def clear_inventory(username):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE inventory_slots
            SET item_template_id = NULL, quantity = 0, item_instance_id = NULL
            WHERE character_id = ?
            """,
            (character_id,),
        )
        conn.execute("DELETE FROM character_artifacts WHERE character_id = ?", (character_id,))
        conn.commit()


def count_action_records(character_id, action_type):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT COUNT(*) FROM action_records WHERE character_id = ? AND action_type = ?", (character_id, action_type)).fetchone()[0]


def table_columns(table_name):
    with sqlite3.connect(DB_PATH) as conn:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}


def count_logs(character_id, log_type=None):
    with sqlite3.connect(DB_PATH) as conn:
        if log_type:
            return conn.execute("SELECT COUNT(*) FROM game_logs WHERE character_id = ? AND type = ?", (character_id, log_type)).fetchone()[0]
        return conn.execute("SELECT COUNT(*) FROM game_logs WHERE character_id = ?", (character_id,)).fetchone()[0]


def main():
    stamp = int(time.time())
    player_a = f"loop_a_{stamp}"
    player_b = f"loop_b_{stamp}"
    player_s = f"sect_s_{stamp}"

    assert request("/dev/health")["ok"] is True
    summary = request("/dev/db-summary")
    for table in [
        "item_templates",
        "inventory_slots",
        "item_instances",
        "character_methods",
        "character_artifacts",
        "character_tasks",
        "game_logs",
        "action_records",
        "sects",
        "sect_members",
        "sect_tasks",
        "sect_reputation_logs",
        "active_effects",
        "life_skill_records",
    ]:
        assert table in summary["tables"]
    assert summary["sects"] >= 8
    simulation_1h = request("/dev/simulation?hours=1")
    simulation_3h = request("/dev/simulation?hours=3")
    simulation_sect = request("/dev/simulation?hours=3&with_sect=true")
    assert simulation_1h["time"] == "1h"
    assert simulation_3h["time"] == "3h"
    assert "realm" in simulation_3h
    assert "warnings" in simulation_3h
    assert "action_counts" in simulation_3h
    assert simulation_1h["action_counts"].get("explore", 0) > 0
    assert simulation_1h["explore_ratio"] >= 0.3
    assert simulation_sect["with_sect"] is True
    assert "sect_tasks_completed" in simulation_sect
    assert "sect_task_type_distribution" in simulation_sect
    assert "sect_reward_by_type" in simulation_sect
    assert "sect_max_task_type_ratio" in simulation_sect
    assert SIMULATION_PATH.exists()

    token_a = register(player_a)["token"]
    token_b = register(player_b)["token"]
    token_s = register(player_s)["token"]
    _user_a_id, character_a_id = get_ids(player_a)
    _user_s_id, character_s_id = get_ids(player_s)

    me_a = request("/character/me", token=token_a)
    me_b = request("/character/me", token=token_b)
    assert me_a["username"] == player_a
    assert me_b["username"] == player_b
    assert len(me_a["inventory"]) == 81
    assert me_a["active_task"]["id"] == "task_001"
    assert me_a["active_task"]["progress"] == 0
    assert "action_points" not in table_columns("characters")
    assert not HIDDEN_FIELDS.intersection(me_a["character"].keys())

    force_character(player_b, hp=0, mana=40)
    dead_explore = action(token_b, "explore")
    assert dead_explore["success"] is False
    assert "陨落" in dead_explore["message"]
    dead_recover = action(token_b, "recover_mana_meditate")
    assert dead_recover["success"] is False
    assert "陨落" in dead_recover["message"]
    assert request("/character/me", token=token_b)["character"]["mana"] == 40
    force_character(player_b, hp=100, mana=100)

    sects = request("/sects")
    assert len(sects) >= 8
    assert {sect["faction"] for sect in sects} >= {"righteous", "demonic", "ghost", "buddhist"}
    force_character(player_s, realm="炼气五层", realm_stage="炼气", cultivation_cap=330, mana=500, spirit_stones=500)
    joined = action(token_s, "join_sect", {"sect_code": "qingxuan_sword_sect"})
    assert joined["success"] is True
    assert joined["sect"]["code"] == "qingxuan_sword_sect"
    sect_me = request("/sects/me", token=token_s)
    assert sect_me["sect"]["name"] == "青玄剑宗"
    assert sect_me["member"]["position"] == "outer_disciple"
    second_join = action(token_s, "join_sect", {"sect_code": "taiqing_alchemy_pavilion"})
    assert second_join["success"] is False
    sect_tasks = request("/sects/tasks", token=token_s)
    assert any(task["code"] == "patrol_mountain" for task in sect_tasks)
    accepted = action(token_s, "accept_sect_task", {"task_code": "patrol_mountain"})
    assert accepted["success"] is True
    early_claim = action(token_s, "complete_sect_task")
    assert early_claim["success"] is False
    force_character(player_s, mana=500)
    assert action(token_s, "explore")["success"] is True
    active_task = request("/sects/tasks/me", token=token_s)[0]
    assert active_task["status"] == "active"
    assert active_task["progress"] == 1
    assert action(token_s, "explore")["success"] is True
    active_task = request("/sects/tasks/me", token=token_s)[0]
    assert active_task["status"] == "claimable"
    assert active_task["progress"] == active_task["target"]
    before_contribution = request("/sects/me", token=token_s)["member"]["contribution"]
    completed = action(token_s, "complete_sect_task")
    assert completed["success"] is True
    after_sect = request("/sects/me", token=token_s)
    assert after_sect["member"]["contribution"] > before_contribution
    assert after_sect["reputations"]["righteous"] > 0
    assert count_logs(character_s_id, "sect") >= 2
    assert count_action_records(character_s_id, "complete_sect_task") >= 1
    force_active_sect_member(player_s, contribution=220)
    exchanged = action(token_s, "exchange_sect_reward", {"reward_code": "sect_mana_pill"})
    assert exchanged["success"] is True
    force_active_sect_member(player_s, contribution=150)
    promoted = action(token_s, "promote_sect_position")
    assert promoted["success"] is True
    assert request("/sects/me", token=token_s)["member"]["position"] == "inner_disciple"
    fill_inventory(player_s)
    force_active_sect_member(player_s, contribution=500)
    full_exchange = action(token_s, "exchange_sect_reward", {"reward_code": "sect_artifact"})
    assert full_exchange["success"] is False
    left = action(token_s, "leave_sect")
    assert left["success"] is True
    assert request("/sects/me", token=token_s)["sect"] is None
    rejoined = action(token_s, "join_sect", {"sect_code": "taiqing_alchemy_pavilion"})
    assert rejoined["success"] is True

    force_character(player_s, mana=500)
    clear_inventory(player_s)
    add_item_to_bag(player_s, "low_material", 10)
    add_item_to_bag(player_s, "low_spirit_stone", 40)
    add_item_to_bag(player_s, "broken_jade_slip", 2)
    add_item_to_bag(player_s, "black_iron_shard", 1)
    crafted_pill = action(token_s, "alchemy", {"recipe_id": "alchemy_mana_pill"})
    assert crafted_pill["success"] is True
    crafted_talisman = action(token_s, "talisman", {"recipe_id": "talisman_scout"})
    assert crafted_talisman["success"] is True
    talisman_slot = first_slot_with_code(player_s, "scout_talisman")
    assert talisman_slot is not None
    used_talisman = action(token_s, "use_item", {"slot_index": talisman_slot})
    assert used_talisman["success"] is True
    assert used_talisman["character"]["scout_talisman_charges"] >= 1
    crafted_artifact = action(token_s, "crafting", {"recipe_id": "craft_low_sword"})
    assert crafted_artifact["success"] is True
    force_character(player_s, realm=REALM_NAMES[2], realm_stage="炼气", mana=500)
    add_item_to_bag(player_s, "low_material", 3)
    add_item_to_bag(player_s, "low_spirit_stone", 16)
    formed = action(token_s, "formation", {"recipe_id": "formation_gather_spirit"})
    assert formed["success"] is True
    assert any(effect["effect_type"] == "train_cultivation_bonus" for effect in formed["character"]["active_effects"])
    trained_with_formation = action(token_s, "train")
    assert trained_with_formation["success"] is True
    assert trained_with_formation["character"]["active_effects"]
    _user_s_id, character_s_id = get_ids(player_s)
    with sqlite3.connect(DB_PATH) as conn:
        assert conn.execute("SELECT COUNT(*) FROM life_skill_records WHERE character_id = ?", (character_s_id,)).fetchone()[0] >= 3
        assert conn.execute("SELECT COUNT(*) FROM active_effects WHERE character_id = ?", (character_s_id,)).fetchone()[0] >= 1

    # Life skills v2: test new recipes
    recipes = request("/life-skills/recipes")
    assert len(recipes["alchemy"]) >= 6, f"alchemy: expected >=6, got {len(recipes['alchemy'])}"
    assert len(recipes["talisman"]) >= 6, f"talisman: expected >=6, got {len(recipes['talisman'])}"
    assert len(recipes["crafting"]) >= 6, f"crafting: expected >=6, got {len(recipes['crafting'])}"
    assert len(recipes["formation"]) >= 3, f"formation: expected >=3, got {len(recipes['formation'])}"
    new_ids = {
        "alchemy_yangqi_pill", "alchemy_guyu_pill", "alchemy_huichun_pill",
        "talisman_explore_luck", "talisman_avoid_harm", "talisman_spirit_gather",
        "craft_qingmu_pendant", "craft_juqi_jade", "craft_hushen_bell",
    }
    all_recipe_ids = {r["id"] for skill in recipes.values() for r in skill}
    missing = new_ids - all_recipe_ids
    assert not missing, f"Missing new recipe IDs: {missing}"
    for skill_type, recipe_list in recipes.items():
        for recipe in recipe_list:
            for field in ["id", "name", "skill_type", "mana_cost"]:
                assert field in recipe, f"Recipe {recipe['id']} missing field '{field}'"
            assert "output_item_id" in recipe or "output_effect_id" in recipe, f"Recipe {recipe['id']} missing output"

    # Test new pill items
    add_item_to_bag(player_s, "healing_herb", 10)
    add_item_to_bag(player_s, "low_spirit_stone", 30)
    hp_before = request("/character/me", token=token_s)["character"]["hp"]
    # huichun_pill: recover_hp=40
    slot_huichun = add_item_to_bag(player_s, "huichun_pill")
    used_huichun = action(token_s, "use_item", {"slot_index": slot_huichun})
    assert used_huichun["success"] is True
    hp_after = used_huichun["character"]["hp"]
    assert hp_after > hp_before, f"huichun_pill should restore HP"

    # Test yangqi_pill: train_next_bonus active effect
    slot_yangqi = add_item_to_bag(player_s, "yangqi_pill")
    used_yangqi = action(token_s, "use_item", {"slot_index": slot_yangqi})
    assert used_yangqi["success"] is True
    active_effects = used_yangqi["character"]["active_effects"]
    assert any(e["effect_type"] == "train_next_bonus" for e in active_effects), f"yangqi_pill should activate train_next_bonus: {active_effects}"

    # Test guyu_pill: breakthrough_next_bonus active effect
    slot_guyu = add_item_to_bag(player_s, "guyu_pill")
    used_guyu = action(token_s, "use_item", {"slot_index": slot_guyu})
    assert used_guyu["success"] is True
    active_effects_g = used_guyu["character"]["active_effects"]
    assert any(e["effect_type"] == "breakthrough_next_bonus" for e in active_effects_g), f"guyu_pill should activate breakthrough_next_bonus"

    # Test new talismans
    slot_explore_luck = add_item_to_bag(player_s, "explore_luck_talisman")
    used_talisman2 = action(token_s, "use_item", {"slot_index": slot_explore_luck})
    assert used_talisman2["success"] is True
    effects2 = used_talisman2["character"]["active_effects"]
    assert any(e["effect_type"] == "explore_luck_bonus" for e in effects2), f"explore_luck_talisman should activate explore_luck_bonus"

    slot_avoid_harm = add_item_to_bag(player_s, "avoid_harm_talisman")
    used_avoid = action(token_s, "use_item", {"slot_index": slot_avoid_harm})
    assert used_avoid["success"] is True
    effects_avoid = used_avoid["character"]["active_effects"]
    assert any(e["effect_type"] == "explore_damage_reduction" for e in effects_avoid), f"avoid_harm_talisman should activate explore_damage_reduction"

    slot_spirit_gather = add_item_to_bag(player_s, "spirit_gather_talisman")
    used_spirit = action(token_s, "use_item", {"slot_index": slot_spirit_gather})
    assert used_spirit["success"] is True
    effects_spirit = used_spirit["character"]["active_effects"]
    assert any(e["effect_type"] == "train_cultivation_bonus" for e in effects_spirit), f"spirit_gather_talisman should activate train_cultivation_bonus"

    # Test new crafting recipes (verify success, item ends up in inventory)
    # Note: player_s realm is set to REALM_NAMES[2] (炼气三层) above.
    # craft_hushen_bell requires REALM_NAMES[3] (炼气四层), so set to 炼气四层 first.
    force_character(player_s, realm=REALM_NAMES[3], realm_stage="炼气", mana=500)
    add_item_to_bag(player_s, "low_material", 20)
    add_item_to_bag(player_s, "low_spirit_stone", 60)
    crafted_qingmu = action(token_s, "crafting", {"recipe_id": "craft_qingmu_pendant"})
    assert crafted_qingmu["success"] is True
    slot_qingmu = first_slot_with_code(player_s, "qingmu_pendant")
    assert slot_qingmu is not None, "qingmu_pendant should be in inventory after crafting"

    crafted_juqi = action(token_s, "crafting", {"recipe_id": "craft_juqi_jade"})
    assert crafted_juqi["success"] is True
    slot_juqi = first_slot_with_code(player_s, "juqi_jade")
    assert slot_juqi is not None, "juqi_jade should be in inventory after crafting"

    crafted_hushen = action(token_s, "crafting", {"recipe_id": "craft_hushen_bell"})
    assert crafted_hushen["success"] is True
    slot_hushen = first_slot_with_code(player_s, "hushen_bell")
    assert slot_hushen is not None, "hushen_bell should be in inventory after crafting"

    # Test train_next_bonus: must be consumed after successful training
    add_item_to_bag(player_s, "healing_herb", 2)
    slot_yangqi2 = add_item_to_bag(player_s, "yangqi_pill")
    used_yangqi2 = action(token_s, "use_item", {"slot_index": slot_yangqi2})
    assert used_yangqi2["success"] is True
    effects_before_train = used_yangqi2["character"]["active_effects"]
    train_next_active = any(e["effect_type"] == "train_next_bonus" for e in effects_before_train)
    assert train_next_active, f"train_next_bonus should be active before training: {effects_before_train}"
    # Train once
    train_result = action(token_s, "train")
    assert train_result["success"] is True
    # After training, train_next_bonus should be consumed (expired/removed)
    remaining_effects = train_result["character"]["active_effects"]
    train_next_still_active = any(e["effect_type"] == "train_next_bonus" for e in remaining_effects)
    assert not train_next_still_active, f"train_next_bonus should be consumed after training: {remaining_effects}"

    # Test breakthrough_next_bonus: must be consumed after breakthrough attempt
    # Set up player_s for breakthrough (REALM_NAMES[3] = 炼气四层 -> 炼气五层)
    force_character(player_s, realm=REALM_NAMES[3], realm_stage="炼气", cultivation_cap=480, cultivation=480, mana=1000, hidden_luck=0, hidden_inner_demon=0)
    add_item_to_bag(player_s, "low_material", 3)
    add_item_to_bag(player_s, "healing_herb", 9)
    add_item_to_bag(player_s, "low_spirit_stone", 36)
    slot_guyu2 = add_item_to_bag(player_s, "guyu_pill")
    used_guyu2 = action(token_s, "use_item", {"slot_index": slot_guyu2})
    assert used_guyu2["success"] is True
    effects_guyu_before = used_guyu2["character"]["active_effects"]
    bt_next_active = any(e["effect_type"] == "breakthrough_next_bonus" for e in effects_guyu_before)
    assert bt_next_active, f"breakthrough_next_bonus should be active before breakthrough: {effects_guyu_before}"
    # Attempt breakthrough
    bt_result = action(token_s, "breakthrough")
    # Either success or failure, effect should be consumed
    remaining_bt_effects = bt_result["character"]["active_effects"]
    bt_next_still_active = any(e["effect_type"] == "breakthrough_next_bonus" for e in remaining_bt_effects)
    assert not bt_next_still_active, f"breakthrough_next_bonus should be consumed after breakthrough attempt: {remaining_bt_effects}"

    # Test qingmu_pendant: stats change after equipping
    force_character(player_s, realm=REALM_NAMES[3], realm_stage="炼气", mana=500)
    clear_inventory(player_s)
    add_item_to_bag(player_s, "low_material", 4)
    add_item_to_bag(player_s, "low_spirit_stone", 10)
    crafted_qingmu2 = action(token_s, "crafting", {"recipe_id": "craft_qingmu_pendant"})
    assert crafted_qingmu2["success"] is True
    slot_qingmu2 = first_slot_with_code(player_s, "qingmu_pendant")
    assert slot_qingmu2 is not None
    me_before_equip = request("/character/me", token=token_s)
    attack_before_qingmu = me_before_equip["character"]["attack"]
    defense_before_qingmu = me_before_equip["character"]["defense"]
    equipped_qingmu = action(token_s, "equip_artifact", {"slot_index": slot_qingmu2})
    assert equipped_qingmu["success"] is True
    me_after_equip = request("/character/me", token=token_s)
    attack_after_qingmu = me_after_equip["character"]["attack"]
    assert attack_after_qingmu > attack_before_qingmu, f"attack should increase after equipping qingmu_pendant: before={attack_before_qingmu}, after={attack_after_qingmu}"

    # Test juqi_jade: attack/defense changes after equipping
    clear_inventory(player_s)
    add_item_to_bag(player_s, "low_material", 4)
    add_item_to_bag(player_s, "low_spirit_stone", 12)
    crafted_juqi2 = action(token_s, "crafting", {"recipe_id": "craft_juqi_jade"})
    assert crafted_juqi2["success"] is True
    slot_juqi2 = first_slot_with_code(player_s, "juqi_jade")
    assert slot_juqi2 is not None
    me_before_juqi = request("/character/me", token=token_s)
    attack_before_juqi = me_before_juqi["character"]["attack"]
    defense_before_juqi = me_before_juqi["character"]["defense"]
    equipped_juqi = action(token_s, "equip_artifact", {"slot_index": slot_juqi2})
    assert equipped_juqi["success"] is True
    me_after_juqi = request("/character/me", token=token_s)
    attack_after_juqi = me_after_juqi["character"]["attack"]
    defense_after_juqi = me_after_juqi["character"]["defense"]
    assert attack_after_juqi > attack_before_juqi or defense_after_juqi > defense_before_juqi, \
        f"juqi_jade stats should increase after equipping: attack {attack_before_juqi}->{attack_after_juqi}, defense {defense_before_juqi}->{defense_after_juqi}"

    # Test hushen_bell: attack/defense changes after equipping
    clear_inventory(player_s)
    add_item_to_bag(player_s, "low_material", 5)
    add_item_to_bag(player_s, "low_spirit_stone", 14)
    crafted_hushen2 = action(token_s, "crafting", {"recipe_id": "craft_hushen_bell"})
    assert crafted_hushen2["success"] is True
    slot_hushen2 = first_slot_with_code(player_s, "hushen_bell")
    assert slot_hushen2 is not None
    me_before_hushen = request("/character/me", token=token_s)
    attack_before_hushen = me_before_hushen["character"]["attack"]
    defense_before_hushen = me_before_hushen["character"]["defense"]
    equipped_hushen = action(token_s, "equip_artifact", {"slot_index": slot_hushen2})
    assert equipped_hushen["success"] is True
    me_after_hushen = request("/character/me", token=token_s)
    attack_after_hushen = me_after_hushen["character"]["attack"]
    defense_after_hushen = me_after_hushen["character"]["defense"]
    assert attack_after_hushen > attack_before_hushen or defense_after_hushen > defense_before_hushen, \
        f"hushen_bell stats should increase after equipping: attack {attack_before_hushen}->{attack_after_hushen}, defense {defense_before_hushen}->{defense_after_hushen}"

    print("[PASS] Life skills v2: new recipes and items verified")

    force_character(player_a, mana=500, hidden_luck=150)
    for _ in range(5):
        trained = action(token_a, "train")
        assert trained["success"] is True
    train_results = recent_action_results(player_a, "train", 5)
    assert [round(result["data"]["efficiency"], 1) for result in train_results] == [1.0, 0.8, 0.6, 0.4, 0.2]
    me_a = request("/character/me", token=token_a)
    assert me_a["active_task"]["id"] == "task_002"
    assert count_logs(character_a_id, "task") >= 1

    force_character(player_a, mana=500, hidden_luck=150)
    explored = action(token_a, "explore", {"force_lucky_code": "hidden_cave"})
    assert explored["success"] is True
    assert any(reward["type"] == "item" for reward in explored["rewards"])
    assert action(token_a, "explore")["success"] is True
    assert action(token_a, "explore")["success"] is True
    assert request("/character/me", token=token_a)["active_task"]["id"] == "task_003"
    assert any(slot["name"] for slot in request("/inventory", token=token_a))
    assert count_logs(character_a_id, "drop") >= 1
    assert count_logs(character_a_id, "lucky") >= 1

    method_slot = add_item_to_bag(player_a, "low_method")
    before_speed = request("/character/me", token=token_a)["character"]["cultivation_speed"]
    learned = action(token_a, "learn_method", {"slot_index": method_slot})
    assert learned["success"] is True
    assert request("/character/me", token=token_a)["active_task"]["id"] == "task_004"
    methods = request("/methods", token=token_a)
    assert len(methods) == 1
    equipped_method = action(token_a, "equip_method", {"method_id": methods[0]["id"]})
    assert equipped_method["success"] is True
    after_speed = request("/character/me", token=token_a)["character"]["cultivation_speed"]
    assert after_speed > before_speed

    set_first_method_to_level(player_a, 1, 55)
    force_character(player_a, mana=100)
    practiced = action(token_a, "practice_method", {"method_id": methods[0]["id"]})
    assert practiced["success"] is True
    assert request("/methods", token=token_a)[0]["level"] >= 2
    assert count_logs(character_a_id, "method") >= 3

    artifact_slot = add_item_to_bag(player_a, "low_artifact", rarity="白")
    before_attack = request("/character/me", token=token_a)["character"]["attack"]
    equipped_artifact = action(token_a, "equip_artifact", {"slot_index": artifact_slot})
    assert equipped_artifact["success"] is True
    assert request("/character/me", token=token_a)["active_task"]["id"] == "task_005"
    artifacts = request("/artifacts", token=token_a)
    assert len(artifacts) == 1
    after_attack = request("/character/me", token=token_a)["character"]["attack"]
    assert after_attack > before_attack
    set_first_artifact_rarity(player_a, "白")
    upgraded = None
    for _ in range(10):
        force_character(player_a, spirit_stones=500)
        upgraded = action(token_a, "upgrade_artifact", {"artifact_id": artifacts[0]["id"]})
        if upgraded["success"]:
            break
    assert upgraded and upgraded["success"] is True
    assert request("/artifacts", token=token_a)[0]["level"] >= 2
    assert count_logs(character_a_id, "artifact") >= 2

    force_character(
        player_a,
        realm="炼气十二层",
        realm_stage="炼气",
        cultivation=2500,
        cultivation_cap=2500,
        mana=1000,
        hidden_luck=120,
        hidden_inner_demon=0,
    )
    set_first_method_to_level(player_a, 3)
    remove_item_from_bag(player_a, "foundation_pill")
    blocked = action(token_a, "breakthrough")
    assert blocked["success"] is False
    assert "缺少筑基丹" in blocked["message"]

    add_item_to_bag(player_a, "foundation_pill")
    blocked_by_explore = action(token_a, "breakthrough")
    assert blocked_by_explore["success"] is False
    assert "探索" in blocked_by_explore["message"]
    add_explore_records(player_a, 20)
    unlocked = action(token_a, "breakthrough")
    assert unlocked["success"] is True
    assert unlocked["character"]["realm"] == "筑基初期"
    assert count_logs(character_a_id, "breakthrough") >= 2

    lucky = action(token_a, "explore", {"force_lucky_code": "master_teach"})
    assert lucky["success"] is True
    assert count_logs(character_a_id, "lucky") >= 2

    untouched_b = request("/character/me", token=token_b)
    assert untouched_b["username"] == player_b
    assert untouched_b["character"]["realm"] == "炼气一层"
    assert request("/methods", token=token_b) == []
    assert request("/artifacts", token=token_b) == []

    relogin_token = login(player_a)
    persisted = request("/character/me", token=relogin_token)
    assert persisted["character"]["realm"] == "筑基初期"
    assert request("/methods", token=relogin_token)[0]["level"] >= 3
    assert request("/artifacts", token=relogin_token)[0]["level"] >= 2

    # Life Skills Recipes API
    recipes = request("/life-skills/recipes")
    assert "alchemy" in recipes
    assert "talisman" in recipes
    assert "crafting" in recipes
    assert "formation" in recipes
    for skill_type in ["alchemy", "talisman", "crafting", "formation"]:
        assert len(recipes[skill_type]) >= 1
        for recipe in recipes[skill_type]:
            assert "id" in recipe
            assert "name" in recipe
            assert "skill_type" in recipe
            assert "mana_cost" in recipe
            assert "output_item_id" in recipe or "output_effect_id" in recipe

    print("Smoke test passed.")


if __name__ == "__main__":
    main()
