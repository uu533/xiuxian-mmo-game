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

from tests.test_server_utils import ensure_test_server
ensure_test_server()

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
# Dev routes are gated by ENABLE_DEV_ROUTES (default off for security).
# Set to enable /dev/* endpoints in smoke test.
os.environ.setdefault("ENABLE_DEV_ROUTES", "1")
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


def assert_no_raw_code(text, label=""):
    """Check that text doesn't contain raw item codes"""
    matches = RAW_CODE_RE.findall(text or "")
    bad_codes = [m for m in matches if m not in {"api", "url", "id"} and not any(safe in m for safe in ["_id", "_code", "item_id", "task_id"])]
    if bad_codes:
        raise AssertionError(f"{label}: Found raw codes: {bad_codes}\nText: {text[:200]}")


def assert_chinese(text, label=""):
    """Check that text contains Chinese characters and no raw codes."""
    assert_no_raw_code(text, label)
    has_cjk = any('\u4e00' <= c <= '\u9fff' for c in (text or ""))
    assert has_cjk, f"{label}: No Chinese characters found in: {text[:200]}"


def register_user():
    username = f"goalqa_{int(time.time() * 1000)}"
    token = request("/register", "POST", payload={"username": username, "password": "123456"})["token"]
    return username, token


def get_ids(username):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT users.id, characters.id FROM users JOIN characters ON characters.user_id = users.id WHERE users.username = ?",
            (username,),
        ).fetchone()
    assert row, f"User {username} not found"
    return row[0], row[1]


def force_character(username, **fields):
    _user_id, character_id = get_ids(username)
    assignments = ", ".join(f"{name} = ?" for name in fields)
    values = list(fields.values()) + [character_id]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"UPDATE characters SET {assignments} WHERE id = ?", values)
        conn.commit()


def get_stones(username):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT spirit_stones FROM characters WHERE id = ?", (character_id,)).fetchone()
        return row[0] if row else 0


def get_contribution(username):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT contribution FROM sect_members WHERE character_id = ? AND status = 'active'", (character_id,)).fetchone()
        return row[0] if row else 0


def get_active_task_count(username):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT COUNT(*) FROM sect_tasks WHERE character_id = ? AND status = 'active'", (character_id,)).fetchone()
        return row[0] if row else 0


def add_item_to_bag(username, code, quantity=1):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        template = conn.execute("SELECT id, stackable FROM item_templates WHERE code = ?", (code,)).fetchone()
        if not template:
            return None
        template_id, stackable = template
        slot = conn.execute(
            "SELECT id FROM inventory_slots WHERE character_id = ? AND container_type = 'main_bag' AND container_id = 0 AND item_template_id IS NULL ORDER BY slot_index LIMIT 1",
            (character_id,),
        ).fetchone()
        if not slot:
            return None
        slot_id = slot[0]
        conn.execute(
            "UPDATE inventory_slots SET item_template_id = ?, quantity = ? WHERE id = ?",
            (template_id, quantity, slot_id),
        )
        conn.commit()
    return slot_id


def main():
    request("/dev/health")

    # Test 1: New account must have long-term goal
    username1, token1 = register_user()
    force_character(username1, realm="炼气三层", realm_stage="炼气", mana=500, max_mana=500, cultivation_cap=330, spirit_stones=100)

    goals_response = request("/goals/current", token=token1)
    assert "goals" in goals_response, "Response should have 'goals' key"
    assert isinstance(goals_response["goals"], list), "goals should be a list"
    assert len(goals_response["goals"]) <= 3, f"Goals should be at most 3, got {len(goals_response['goals'])}"

    # New account must have BOTH short_term and long_term
    short_count = sum(1 for g in goals_response["goals"] if g["category"] == "short_term")
    long_count = sum(1 for g in goals_response["goals"] if g["category"] == "long_term")
    assert short_count >= 1, f"New account should have at least 1 short_term goal, got {short_count}"
    assert long_count >= 1, f"New account should have at least 1 long_term goal, got {long_count}"
    assert short_count <= 2, f"short_term goals should be at most 2, got {short_count}"
    assert long_count <= 1, f"long_term goals should be at most 1, got {long_count}"

    # Test 2: Each goal has required fields
    for goal in goals_response["goals"]:
        assert "id" in goal, "Goal should have 'id'"
        assert "category" in goal, "Goal should have 'category'"
        assert "title" in goal, "Goal should have 'title'"
        assert "reason" in goal, "Goal should have 'reason'"
        assert "progress_text" in goal, "Goal should have 'progress_text'"
        assert "requirements" in goal, "Goal should have 'requirements'"
        assert "recommended_action" in goal, "Goal should have 'recommended_action'"
        assert "benefits" in goal, "Goal should have 'benefits'"
        assert "priority" in goal, "Goal should have 'priority'"
        assert goal["category"] in ["short_term", "long_term"], f"Invalid category: {goal['category']}"

    # Test 3: All player-visible text is Chinese
    for goal in goals_response["goals"]:
        assert_chinese(goal["title"], "goal title")
        assert_chinese(goal["reason"], "goal reason")
        if goal.get("progress_text"):
            assert_chinese(goal["progress_text"], "goal progress_text")
        for req in goal.get("requirements", []):
            assert_chinese(req, "goal requirement")
        assert_chinese(goal["recommended_action"], "goal recommended_action")
        assert_chinese(goal["benefits"], "goal benefits")

    # Test 4: No raw codes in any field
    for goal in goals_response["goals"]:
        assert_no_raw_code(goal["title"], "goal title")
        assert_no_raw_code(goal["reason"], "goal reason")
        for req in goal.get("requirements", []):
            assert_no_raw_code(req, "goal requirement")
        assert_no_raw_code(goal["recommended_action"], "goal recommended_action")
        assert_no_raw_code(goal["benefits"], "goal benefits")

    # Test 5: Goals API is read-only - player state unchanged
    stones_before = get_stones(username1)
    contribution_before = get_contribution(username1)
    task_count_before = get_active_task_count(username1)

    goals_response2 = request("/goals/current", token=token1)
    goals_response3 = request("/goals/current", token=token1)

    stones_after = get_stones(username1)
    contribution_after = get_contribution(username1)
    task_count_after = get_active_task_count(username1)

    assert stones_after == stones_before, f"Stones changed: {stones_before} -> {stones_after}"
    assert contribution_after == contribution_before, f"Contribution changed: {contribution_before} -> {contribution_after}"
    assert task_count_after == task_count_before, f"Task count changed: {task_count_before} -> {task_count_after}"

    # Test 6: Sect task goal when in sect with active task
    username2, token2 = register_user()
    force_character(username2, realm="炼气三层", realm_stage="炼气", mana=500, max_mana=500, spirit_stones=200)

    join_result = action(token2, "join_sect", {"sect_code": "qingxuan_sword_sect"})
    assert join_result["success"], f"Join sect failed: {join_result.get('message')}"

    accept_result = action(token2, "accept_sect_task", {"task_code": "patrol_mountain"})
    assert accept_result["success"], f"Accept task failed: {accept_result.get('message')}"

    goals_with_task = request("/goals/current", token=token2)
    # MUST have sect task goal when player has active sect task
    has_sect_task_goal = any(g["id"] == "sect_task_current" for g in goals_with_task["goals"])
    assert has_sect_task_goal, f"Player with active sect task should have sect_task_current goal, got {[g['id'] for g in goals_with_task['goals']]}"

    sect_task_goal = next(g for g in goals_with_task["goals"] if g["id"] == "sect_task_current")
    assert "宗门任务" in sect_task_goal["title"], f"Sect task goal title should mention 宗门任务: {sect_task_goal['title']}"
    assert_chinese(sect_task_goal["title"], "sect task goal title")

    # Test 7: Breakthrough goal when close to threshold
    username3, token3 = register_user()
    # Set cultivation to 75%+ of cap to trigger breakthrough goal
    force_character(username3, realm="炼气三层", realm_stage="炼气", mana=500, max_mana=500, cultivation_cap=330, cultivation=250, spirit_stones=200)

    goals_breakthrough = request("/goals/current", token=token3)
    assert len(goals_breakthrough["goals"]) >= 1, "Should have at least one goal"
    # MUST have breakthrough-related goal (either specific or fallback)
    has_breakthrough_goal = any("突破" in g["title"] for g in goals_breakthrough["goals"])
    assert has_breakthrough_goal, f"Player with high cultivation should have breakthrough-related goal, got {[g['title'] for g in goals_breakthrough['goals']]}"

    # Test 8: Material explore goal when missing materials
    username4, token4 = register_user()
    force_character(username4, realm="炼气三层", realm_stage="炼气", mana=500, max_mana=500, spirit_stones=10)

    goals_materials = request("/goals/current", token=token4)
    # MUST have material explore goal when low on stones
    has_material_goal = any("探索" in g["title"] or "材料" in g["title"] for g in goals_materials["goals"])
    assert has_material_goal, f"Player with low spirit stones should have material explore goal, got {[g['title'] for g in goals_materials['goals']]}"

    # Test 9: Life skill goal when materials are available
    username5, token5 = register_user()
    force_character(username5, realm="炼气三层", realm_stage="炼气", mana=500, max_mana=500, spirit_stones=200)

    add_item_to_bag(username5, "healing_herb", 3)
    add_item_to_bag(username5, "low_spirit_stone", 10)

    goals_with_life = request("/goals/current", token=token5)
    # MUST have life skill goal when materials are available
    has_life_skill_goal = any("炼制" in g["title"] for g in goals_with_life["goals"])
    assert has_life_skill_goal, f"Player with crafting materials should have life skill goal, got {[g['title'] for g in goals_with_life['goals']]}"

    # Test 10: No hidden properties leak
    for goal in goals_with_life["goals"]:
        goal_text = " ".join([
            goal.get("title", ""),
            goal.get("reason", ""),
            goal.get("recommended_action", ""),
            goal.get("benefits", ""),
        ])
        assert "luck" not in goal_text.lower() or "机缘" in goal_text, f"Hidden property leak in goal: {goal['title']}"
        assert "inner_demon" not in goal_text.lower(), f"Hidden property leak in goal: {goal['title']}"
        assert "心魔" not in goal_text, f"Hidden property leak in goal: {goal['title']}"

    # Test 11: Repeated calls return consistent results
    goals_first = request("/goals/current", token=token1)
    goals_second = request("/goals/current", token=token1)
    assert len(goals_first["goals"]) == len(goals_second["goals"]), "Goal count should be consistent"

    print("Goal chain player flow test passed.")


if __name__ == "__main__":
    main()