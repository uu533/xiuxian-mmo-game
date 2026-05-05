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


def force_ready_for_breakthrough(username, luck, inner_demon):
    with sqlite3.connect(DB_PATH) as conn:
        user_id = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()[0]
        conn.execute(
            """
            UPDATE characters
            SET cultivation = cultivation_cap, luck = ?, inner_demon = ?, action_points = 100
            WHERE user_id = ?
            """,
            (luck, inner_demon, user_id),
        )
        conn.commit()


def force_realm(username, realm, cultivation_cap=17000, action_points=100):
    with sqlite3.connect(DB_PATH) as conn:
        user_id = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()[0]
        conn.execute(
            """
            UPDATE characters
            SET realm = ?, cultivation = 0, cultivation_cap = ?, action_points = ?
            WHERE user_id = ?
            """,
            (realm, cultivation_cap, action_points, user_id),
        )
        conn.commit()


def force_age_progress(username, age_progress, action_points=100):
    with sqlite3.connect(DB_PATH) as conn:
        user_id = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()[0]
        conn.execute(
            """
            UPDATE characters
            SET age_progress = ?, action_points = ?
            WHERE user_id = ?
            """,
            (age_progress, action_points, user_id),
        )
        conn.commit()


def main():
    stamp = int(time.time())
    player_a = f"test_a_{stamp}"
    player_b = f"test_b_{stamp}"

    token_a = register(player_a)["token"]
    token_b = register(player_b)["token"]

    me_a = request("/me", token=token_a)
    me_b = request("/me", token=token_b)
    assert me_a["username"] == player_a
    assert me_b["username"] == player_b
    assert me_a["character"]["realm"] == "炼气一层"
    assert me_a["character"]["cultivation_cap"] == 80
    assert me_a["character"]["title"] in ("师兄", "师姐")
    assert "师姐" in me_a["character"]["unlocked_titles"]
    assert me_a["character"]["life_status"] == "存活"
    assert me_a["character"]["spiritual_root"].endswith(VALID_ROOT_SUFFIXES)
    assert me_a["character"]["spirit_stones"] == 100
    assert me_b["character"]["spirit_stones"] == 100
    assert me_a["character"]["action_points"] == 100
    assert me_a["character"]["max_action_points"] == 100

    trained = request("/action/train", "POST", token=token_a)
    assert trained["character"]["cultivation"] > me_a["character"]["cultivation"]
    assert trained["character"]["age"] == me_a["character"]["age"]
    assert trained["character"]["lifespan"] == me_a["character"]["lifespan"]
    assert trained["character"]["action_points"] == me_a["character"]["action_points"] - 10

    explored = request("/action/explore", "POST", token=token_a)
    assert explored["message"]
    assert explored["character"]["action_points"] == trained["character"]["action_points"] - 15

    title_changed = request("/character/title", "POST", token=token_a, payload={"title": "师姐"})
    assert title_changed["character"]["title"] == "师姐"
    locked_title = request("/character/title", "POST", token=token_a, payload={"title": "真人"})
    assert locked_title["character"]["title"] == "师姐"
    assert "尚未解锁" in locked_title["message"]

    force_realm(player_a, "结丹初期")
    unlocked_title = request("/character/title", "POST", token=token_a, payload={"title": "真人"})
    assert unlocked_title["character"]["title"] == "真人"

    force_age_progress(player_a, age_progress=990, action_points=100)
    aged = request("/action/train", "POST", token=token_a)
    assert aged["character"]["age"] == me_a["character"]["age"] + 1
    assert aged["character"]["age_progress"] == 0

    untouched_b = request("/me", token=token_b)
    assert untouched_b["character"]["cultivation"] == me_b["character"]["cultivation"]
    assert untouched_b["character"]["spirit_stones"] == me_b["character"]["spirit_stones"]

    logs_a = request("/logs", token=token_a)
    logs_b = request("/logs", token=token_b)
    assert len(logs_a) >= 3
    assert len(logs_b) >= 2
    assert all("test_a" not in log["content"] for log in logs_b)

    force_realm(player_a, "炼气一层", cultivation_cap=80)
    force_ready_for_breakthrough(player_a, luck=120, inner_demon=0)
    success = request("/action/breakthrough", "POST", token=token_a)
    assert "突破成功" in success["message"]
    assert success["character"]["realm"] == "炼气二层"

    force_ready_for_breakthrough(player_b, luck=0, inner_demon=100)
    failure = request("/action/breakthrough", "POST", token=token_b)
    assert "突破失败" in failure["message"]

    persisted = request("/me", token=token_a)
    assert persisted["character"]["realm"] == success["character"]["realm"]

    print("Smoke test passed.")


if __name__ == "__main__":
    main()
