import json
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
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

    print("Smoke test passed.")


if __name__ == "__main__":
    main()
