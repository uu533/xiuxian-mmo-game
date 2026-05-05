import json
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "game.db"
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


def action(token, action_type, params=None):
    return request("/action/execute", "POST", token=token, payload={"action_type": action_type, "params": params or {}})


def login(username):
    return request("/login", "POST", payload={"username": username, "password": "123456"})["token"]


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


def add_mana_pill_to_first_slot(username):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        template_id = conn.execute("SELECT id FROM item_templates WHERE code = 'mana_pill'").fetchone()[0]
        conn.execute(
            """
            UPDATE inventory_slots
            SET item_template_id = ?, quantity = 1, item_instance_id = NULL
            WHERE id = (
                SELECT id FROM inventory_slots
                WHERE character_id = ? AND container_type = 'main_bag' AND container_id = 0
                ORDER BY slot_index
                LIMIT 1
            )
            """,
            (template_id, character_id),
        )
        conn.commit()


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
    player_a = f"refactor_a_{stamp}"
    player_b = f"refactor_b_{stamp}"

    assert request("/dev/health")["ok"] is True
    summary = request("/dev/db-summary")
    for table in ["item_templates", "inventory_slots", "game_logs", "action_records", "sects", "friendships", "messages"]:
        assert table in summary["tables"]

    token_a = register(player_a)["token"]
    token_b = register(player_b)["token"]
    user_a_id, character_a_id = get_ids(player_a)

    me_a = request("/character/me", token=token_a)
    me_b = request("/character/me", token=token_b)
    assert me_a["username"] == player_a
    assert me_b["username"] == player_b
    assert me_a["character"]["name"] == player_a
    assert me_a["character"]["realm"] == "炼气一层"
    assert me_a["character"]["hp"] <= me_a["character"]["max_hp"]
    assert me_a["character"]["mana"] <= me_a["character"]["max_mana"]
    assert me_a["character"]["attack"] == me_a["character"]["base_attack"] + me_a["character"]["attack_bonus"]
    assert me_a["character"]["defense"] == me_a["character"]["base_defense"] + me_a["character"]["defense_bonus"]
    assert not HIDDEN_FIELDS.intersection(me_a["character"].keys())
    assert "action_points" not in table_columns("characters")

    inventory = request("/inventory", token=token_a)
    assert len(inventory) == 81
    assert inventory[0]["slot_index"] == 1

    before_mana = me_a["character"]["mana"]
    before_cultivation = me_a["character"]["cultivation"]
    trained = action(token_a, "train")
    assert trained["success"] is True
    assert trained["character"]["mana"] == before_mana - 12
    assert trained["character"]["cultivation"] > before_cultivation

    force_character(player_a, mana=0)
    failed_train = action(token_a, "train")
    assert failed_train["success"] is False
    assert "法力不足" in failed_train["message"]

    meditated = action(token_a, "recover_mana_meditate")
    assert meditated["success"] is True
    assert meditated["character"]["mana"] > 0

    force_character(player_a, mana=0, spirit_stones=100)
    stone_recovered = action(token_a, "recover_mana_stone")
    assert stone_recovered["success"] is True
    assert stone_recovered["character"]["mana"] == 60
    assert stone_recovered["character"]["spirit_stones"] == 90

    add_mana_pill_to_first_slot(player_a)
    force_character(player_a, mana=0)
    used_item = action(token_a, "use_item", {"slot_index": 1})
    assert used_item["success"] is True
    assert used_item["character"]["mana"] == used_item["character"]["max_mana"]

    item_seen = False
    event_seen = False
    for _ in range(25):
        force_character(player_a, mana=100, hp=100)
        explored = action(token_a, "explore")
        assert explored["message"]
        assert explored["cost"]["mana"] == 18
        event_seen = True
        if any(reward.get("type") == "item" for reward in explored["rewards"]):
            item_seen = True
            break
    assert event_seen is True
    assert item_seen is True
    assert count_logs(character_a_id, "explore") >= 1

    force_character(player_a, realm="炼气一层", realm_stage="炼气", cultivation=80, cultivation_cap=80, mana=1000, hidden_luck=120, hidden_inner_demon=0)
    breakthrough_success = action(token_a, "breakthrough")
    assert breakthrough_success["success"] is True
    assert "突破成功" in breakthrough_success["message"]
    assert count_logs(character_a_id, "breakthrough") >= 1

    force_character(player_b, cultivation=80, cultivation_cap=80, mana=1000, hidden_luck=0, hidden_inner_demon=100)
    breakthrough_failure = action(token_b, "breakthrough")
    assert breakthrough_failure["success"] is False
    assert "突破失败" in breakthrough_failure["message"]

    logs = request("/logs", token=token_a)
    assert logs
    assert {"id", "type", "content", "data_json", "created_at"}.issubset(logs[0].keys())

    relogin_token = login(player_a)
    persisted = request("/character/me", token=relogin_token)
    assert persisted["character"]["realm"] == breakthrough_success["character"]["realm"]
    assert persisted["character"]["id"] == character_a_id
    assert get_ids(player_a)[0] == user_a_id

    untouched_b = request("/character/me", token=token_b)
    assert untouched_b["username"] == player_b
    assert untouched_b["character"]["id"] != character_a_id

    print("Smoke test passed.")


if __name__ == "__main__":
    main()
