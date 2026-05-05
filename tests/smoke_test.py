import json
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "game.db"
VALID_ROOT_SUFFIXES = ("天灵根", "双灵根", "三灵根", "伪灵根", "杂灵根", "异灵根")
HIDDEN_FIELDS = {"luck", "inner_demon", "action_points", "max_action_points", "action_spent_total", "age_progress"}


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


def user_id_for(username):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()[0]


def force_ready_for_breakthrough(username, luck, inner_demon, mana=1000):
    with sqlite3.connect(DB_PATH) as conn:
        user_id = user_id_for(username)
        conn.execute(
            """
            UPDATE characters
            SET cultivation = cultivation_cap, luck = ?, inner_demon = ?, mana = ?
            WHERE user_id = ?
            """,
            (luck, inner_demon, mana, user_id),
        )
        conn.commit()


def force_realm(username, realm, cultivation_cap=17000, mana=1000):
    with sqlite3.connect(DB_PATH) as conn:
        user_id = user_id_for(username)
        conn.execute(
            """
            UPDATE characters
            SET realm = ?, cultivation = 0, cultivation_cap = ?, mana = ?
            WHERE user_id = ?
            """,
            (realm, cultivation_cap, mana, user_id),
        )
        conn.commit()


def force_sect(username, sect_name="青云宗", sect_branch="天剑峰"):
    with sqlite3.connect(DB_PATH) as conn:
        user_id = user_id_for(username)
        conn.execute(
            """
            UPDATE characters
            SET sect_name = ?, sect_branch = ?
            WHERE user_id = ?
            """,
            (sect_name, sect_branch, user_id),
        )
        conn.commit()


def force_mana(username, mana, spirit_stones=None):
    with sqlite3.connect(DB_PATH) as conn:
        user_id = user_id_for(username)
        if spirit_stones is None:
            conn.execute("UPDATE characters SET mana = ? WHERE user_id = ?", (mana, user_id))
        else:
            conn.execute(
                "UPDATE characters SET mana = ?, spirit_stones = ? WHERE user_id = ?",
                (mana, spirit_stones, user_id),
            )
        conn.commit()


def add_inventory_item(username, name, quantity=1):
    with sqlite3.connect(DB_PATH) as conn:
        user_id = user_id_for(username)
        conn.execute(
            "INSERT INTO inventory_items (user_id, name, quantity, created_at) VALUES (?, ?, ?, datetime('now'))",
            (user_id, name, quantity),
        )
        conn.commit()


def table_columns(table_name):
    with sqlite3.connect(DB_PATH) as conn:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}


def main():
    stamp = int(time.time())
    player_a = f"test_a_{stamp}"
    player_b = f"test_b_{stamp}"

    token_a = register(player_a)["token"]
    token_b = register(player_b)["token"]

    me_a = request("/me", token=token_a)
    me_b = request("/me", token=token_b)
    character = me_a["character"]
    assert me_a["username"] == player_a
    assert me_b["username"] == player_b
    assert character["realm"] == "炼气一层"
    assert character["cultivation_cap"] == 80
    assert character["title"] in ("师兄", "师姐")
    assert "师姐" in character["unlocked_titles"]
    assert character["life_status"] == "存活"
    assert character["identity_status"] == "散修"
    assert character["sect_position"] == "散修"
    assert character["spiritual_root"].endswith(VALID_ROOT_SUFFIXES)
    assert character["spirit_stones"] == 100
    assert me_b["character"]["spirit_stones"] == 100
    assert character["lifespan"] == 100
    assert character["attack"] == 5
    assert character["defense"] == 5
    assert character["attack"] == character["attack_base"] + character["attack_bonus"]
    assert character["defense"] == character["defense_base"] + character["defense_bonus"]
    assert character["mana"] == 100
    assert character["max_mana"] == 100
    assert len(me_a["inventory"]) == 81
    assert me_a["inventory"][0] == {"slot_index": 1, "name": None, "quantity": 0}
    assert not HIDDEN_FIELDS.intersection(character)
    assert not {"action_points", "max_action_points", "action_spent_total", "age_progress"}.intersection(
        table_columns("characters")
    )

    trained = request("/action/train", "POST", token=token_a)
    assert trained["character"]["cultivation"] > character["cultivation"]
    assert trained["character"]["age"] == character["age"]
    assert trained["character"]["lifespan"] == character["lifespan"]
    assert trained["character"]["mana"] == character["mana"] - 12

    explored = request("/action/explore", "POST", token=token_a)
    assert explored["message"]
    assert explored["character"]["mana"] == trained["character"]["mana"] - 18

    force_mana(player_a, 0)
    insufficient = request("/action/train", "POST", token=token_a)
    assert "法力不足" in insufficient["message"]
    assert "打坐恢复法力" in insufficient["message"]

    meditated = request("/action/meditate", "POST", token=token_a)
    assert meditated["character"]["mana"] > 0

    force_mana(player_a, 0, spirit_stones=100)
    stone_restored = request("/action/spirit-stone", "POST", token=token_a)
    assert stone_restored["character"]["mana"] == 60
    assert stone_restored["character"]["spirit_stones"] == 90

    force_mana(player_a, 0)
    add_inventory_item(player_a, "回灵丹", 1)
    pill_restored = request("/action/pill", "POST", token=token_a)
    assert pill_restored["character"]["mana"] == pill_restored["character"]["max_mana"]
    assert len(pill_restored["inventory"]) == 81

    title_changed = request("/character/title", "POST", token=token_a, payload={"title": "师姐"})
    assert title_changed["character"]["title"] == "师姐"
    locked_title = request("/character/title", "POST", token=token_a, payload={"title": "真人"})
    assert locked_title["character"]["title"] == "师姐"
    assert "尚未解锁" in locked_title["message"]

    force_realm(player_a, "结丹初期")
    force_sect(player_a)
    sect_member = request("/me", token=token_a)
    assert sect_member["character"]["identity_status"] == "青云宗 · 天剑峰长老"
    assert sect_member["character"]["sect_position"] == "天剑峰长老"
    assert sect_member["character"]["lifespan"] == 500
    assert sect_member["character"]["attack_base"] == 180
    unlocked_title = request("/character/title", "POST", token=token_a, payload={"title": "真人"})
    assert unlocked_title["character"]["title"] == "真人"

    untouched_b = request("/me", token=token_b)
    assert untouched_b["character"]["cultivation"] == me_b["character"]["cultivation"]
    assert untouched_b["character"]["spirit_stones"] == me_b["character"]["spirit_stones"]

    logs_a = request("/logs", token=token_a)
    logs_b = request("/logs", token=token_b)
    assert len(logs_a) >= 7
    assert len(logs_b) >= 2
    assert all("test_a" not in log["content"] for log in logs_b)

    force_realm(player_a, "炼气一层", cultivation_cap=80)
    force_ready_for_breakthrough(player_a, luck=120, inner_demon=0)
    success = request("/action/breakthrough", "POST", token=token_a)
    assert "突破成功" in success["message"]
    assert success["character"]["realm"] == "炼气二层"
    assert success["character"]["lifespan"] == 100

    force_ready_for_breakthrough(player_b, luck=0, inner_demon=100)
    failure = request("/action/breakthrough", "POST", token=token_b)
    assert "突破失败" in failure["message"]

    persisted = request("/me", token=token_a)
    assert persisted["character"]["realm"] == success["character"]["realm"]

    print("Smoke test passed.")


if __name__ == "__main__":
    main()
