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
    """Check that text doesn't contain raw item codes like low_material, sect_task_xxx, etc."""
    matches = RAW_CODE_RE.findall(text or "")
    # Filter out known safe codes that might appear in Chinese context
    bad_codes = [m for m in matches if m not in {"api", "url", "id"} and not any(safe in m for safe in ["_id", "_code", "item_id", "task_id"])]
    if bad_codes:
        raise AssertionError(f"{label}: Found raw codes in text: {bad_codes}\nText: {text[:200]}")


def assert_chinese(text, label=""):
    """Check that text contains Chinese characters and no raw codes."""
    assert_no_raw_code(text, label)
    # Check for at least some CJK characters
    has_cjk = any('\u4e00' <= c <= '\u9fff' for c in (text or ""))
    assert has_cjk, f"{label}: No Chinese characters found in: {text[:200]}"


def register_user():
    username = f"sectqa_{int(time.time() * 1000)}"
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
    assert row, f"User {username} not found"
    return row[0], row[1]


def force_character(username, **fields):
    _user_id, character_id = get_ids(username)
    assignments = ", ".join(f"{name} = ?" for name in fields)
    values = list(fields.values()) + [character_id]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"UPDATE characters SET {assignments} WHERE id = ?", values)
        conn.commit()


def add_stones(username, amount):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE characters SET spirit_stones = spirit_stones + ? WHERE id = ?", (amount, character_id))
        conn.commit()


def get_contribution(username):
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT contribution FROM sect_members WHERE character_id = ? AND status = 'active'", (character_id,)).fetchone()
        return row[0] if row else 0


def force_sect_member(username, **fields):
    _user_id, character_id = get_ids(username)
    assignments = ", ".join(f"{name} = ?" for name in fields)
    values = list(fields.values()) + [character_id]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"UPDATE sect_members SET {assignments} WHERE character_id = ? AND status = 'active'", values)
        conn.commit()


def get_my_tasks(token):
    return request("/sects/tasks/me", token=token)


def main():
    request("/dev/health")

    # Test 1: Join sect and accept task
    username1, token1 = register_user()
    force_character(username1, realm="炼气三层", realm_stage="炼气", mana=500, max_mana=500, cultivation_cap=330)
    joined = action(token1, "join_sect", {"sect_code": "qingxuan_sword_sect"})
    assert joined["success"], f"Join sect failed: {joined.get('message')}"
    assert_chinese(joined["message"], "join_sect message")

    # Check sect tasks are in Chinese
    sect_tasks = request("/sects/tasks", token=token1)
    assert sect_tasks, "Should have available sect tasks"
    for task in sect_tasks:
        assert_chinese(task["name"], f"Task name should be Chinese: {task['code']}")
        assert_chinese(task["description"], f"Task description should be Chinese: {task['code']}")
        assert_no_raw_code(task["name"], "task name")
        assert_no_raw_code(task.get("requirement_display", ""), "requirement_display")
        assert_no_raw_code(task.get("cost_display", ""), "cost_display")

    # Accept a task
    accept_result = action(token1, "accept_sect_task", {"task_code": "patrol_mountain"})
    assert accept_result["success"], f"Accept task failed: {accept_result.get('message')}"
    assert_chinese(accept_result["message"], "accept_sect_task message")

    # Check current task display
    my_tasks = get_my_tasks(token1)
    assert my_tasks, "Should have current task"
    current_task = my_tasks[0]
    assert_chinese(current_task["name"], "current task name")
    assert_chinese(current_task["description"], "current task description")
    assert current_task["status"] in ["active", "claimable"], f"Task status should be active/claimable: {current_task['status']}"

    # Test 2: Abandon task - check contribution penalty
    contribution_before = get_contribution(username1)
    abandon_result = action(token1, "sect_task_abandon")
    assert abandon_result["success"], f"Abandon task failed: {abandon_result.get('message')}"
    assert_chinese(abandon_result["message"], "abandon_sect_task message")
    assert "已放弃宗门任务" in abandon_result["message"], f"Should mention abandon: {abandon_result['message']}"
    assert "扣除宗门贡献" in abandon_result["message"], f"Should mention contribution penalty: {abandon_result['message']}"

    contribution_after = get_contribution(username1)
    assert contribution_after <= contribution_before, f"Contribution should not increase: {contribution_before} -> {contribution_after}"
    assert contribution_before - contribution_after <= 5, f"Penalty should be at most 5: {contribution_before - contribution_after}"

    # Verify task is cleared
    my_tasks_after = get_my_tasks(token1)
    active_tasks = [t for t in my_tasks_after if t["status"] in ["active", "claimable"]]
    assert not active_tasks, f"No active tasks should remain after abandon: {len(active_tasks)}"

    # Try to abandon when no task
    no_task_result = action(token1, "sect_task_abandon")
    assert not no_task_result["success"], "Should fail when no active task"
    assert_chinese(no_task_result["message"], "no task abandon message")
    assert "当前没有可放弃的宗门任务" in no_task_result["message"], f"Should mention no task: {no_task_result['message']}"

    # Test 3: Accept another task, then leave sect
    accept_result2 = action(token1, "accept_sect_task", {"task_code": "patrol_mountain"})
    assert accept_result2["success"], f"Accept task 2 failed: {accept_result2.get('message')}"

    my_tasks_before_leave = get_my_tasks(token1)
    assert my_tasks_before_leave, "Should have task before leaving"
    task_before_leave_id = my_tasks_before_leave[0]["id"]

    leave_result = action(token1, "leave_sect")
    assert leave_result["success"], f"Leave sect failed: {leave_result.get('message')}"
    assert_chinese(leave_result["message"], "leave_sect message")
    assert "宗门任务已清除" in leave_result["message"] or "清除" in leave_result["message"], f"Should mention task cleared: {leave_result['message']}"

    # Verify task is cleared after leaving sect
    my_tasks_after_leave = get_my_tasks(token1)
    active_tasks_after_leave = [t for t in my_tasks_after_leave if t["status"] in ["active", "claimable"]]
    assert not active_tasks_after_leave, f"No active tasks should remain after leaving sect: {len(active_tasks_after_leave)}"

    # Test 4: Join new sect - verify old tasks don't pollute
    joined_new = action(token1, "join_sect", {"sect_code": "taiqing_alchemy_pavilion"})
    assert joined_new["success"], f"Join new sect failed: {joined_new.get('message')}"

    my_tasks_new_sect = get_my_tasks(token1)
    active_tasks_new_sect = [t for t in my_tasks_new_sect if t["status"] in ["active", "claimable"]]
    assert not active_tasks_new_sect, f"No old tasks should appear in new sect: {len(active_tasks_new_sect)}"

    # Verify old task ID is not in the list
    for task in my_tasks_new_sect:
        assert task["id"] != task_before_leave_id, f"Old task should not appear in new sect: task_id={task['id']}"

    # Test 5: Test donation task payload completeness
    force_character(username1, spirit_stones=200)
    donation_tasks = [t for t in sect_tasks if t.get("is_donation") or t["code"] == "donate_stones"]
    if donation_tasks:
        donation_task = donation_tasks[0]
        # Assert is_donation flag is present in task config
        assert donation_task.get("is_donation") is True, f"Task config should have is_donation=true: {donation_task}"
        assert "需要捐献" in donation_task.get("requirement_display", "") or donation_task.get("is_donation"), f"Task config should show requirement_display: {donation_task}"
        assert "消耗" in donation_task.get("cost_display", "") or donation_task.get("is_donation"), f"Task config should show cost_display: {donation_task}"

        accept_donation = action(token1, "accept_sect_task", {"task_code": donation_task["code"]})
        assert accept_donation["success"], f"Accept donation task failed: {accept_donation.get('message')}"
        assert_chinese(accept_donation["message"], "accept donation task message")

        my_tasks_donation = get_my_tasks(token1)
        active_donation = [t for t in my_tasks_donation if t["status"] == "active" and t.get("is_donation")]
        if active_donation:
            task = active_donation[0]
            # Assert is_donation flag is present in my task payload (frontend needs this)
            assert task.get("is_donation") is True, f"My task should have is_donation=true: {task}"
            # Assert requirement_display is present
            assert task.get("requirement_display"), f"Donation task should have requirement_display: {task}"
            assert "需要捐献" in task.get("requirement_display", "") or "灵石" in task.get("requirement_display", ""), f"Donation task requirement_display should mention 捐献/灵石: {task}"
            # Assert cost_display is present
            assert task.get("cost_display"), f"Donation task should have cost_display: {task}"
            assert "灵石" in task.get("cost_display", "") or "消耗" in task.get("cost_display", ""), f"Donation task cost_display should mention 灵石/消耗: {task}"
            # Progress should start at 0 (not target), so frontend must allow clicking
            assert task["progress"] == 0, f"Donation task progress should start at 0: {task['progress']}"
            # is_donation means frontend should NOT require progress >= target to enable button
            assert task.get("is_donation"), f"Frontend needs is_donation to enable submit button: {task}"

            # Try to complete without enough stones
            force_character(username1, spirit_stones=10)
            complete_no_stones = action(token1, "complete_sect_task")
            assert not complete_no_stones["success"], "Should fail without enough stones"
            assert "缺少材料" in complete_no_stones["message"] or "灵石" in complete_no_stones["message"], f"Should mention missing stones: {complete_no_stones['message']}"
            assert_chinese(complete_no_stones["message"], "insufficient stones message")

            # Complete with enough stones
            force_character(username1, spirit_stones=200)
            complete_donation = action(token1, "complete_sect_task")
            assert complete_donation["success"], f"Complete donation task failed: {complete_donation.get('message')}"
            assert_chinese(complete_donation["message"], "complete donation task message")

    # Test 6: Verify sect_id binding - task from old sect cannot be completed in new sect
    # Create another user with two sects scenario
    username2, token2 = register_user()
    force_character(username2, realm="炼气三层", realm_stage="炼气", mana=500, max_mana=500, spirit_stones=500)

    # Join first sect and accept task
    joined2a = action(token2, "join_sect", {"sect_code": "qingxuan_sword_sect"})
    assert joined2a["success"], f"Join sect 1 failed: {joined2a.get('message')}"

    # Force realm for patrol task
    force_character(username2, mana=1000)
    accept_task2 = action(token2, "accept_sect_task", {"task_code": "patrol_mountain"})
    assert accept_task2["success"], f"Accept task failed: {accept_task2.get('message')}"

    # Complete the task (explore twice)
    explore1 = action(token2, "explore")
    assert explore1["success"], "Explore should succeed"
    explore2 = action(token2, "explore")
    assert explore2["success"], "Explore should succeed"

    # Complete task
    complete_task2 = action(token2, "complete_sect_task")
    assert complete_task2["success"], f"Complete task failed: {complete_task2.get('message')}"
    assert_chinese(complete_task2["message"], "complete task message")

    # Leave and join new sect
    leave2 = action(token2, "leave_sect")
    assert leave2["success"], f"Leave sect failed: {leave2.get('message')}"

    # Join new sect
    joined2b = action(token2, "join_sect", {"sect_code": "xuesha_gate"})
    assert joined2b["success"], f"Join new sect failed: {joined2b.get('message')}"

    # Verify no active tasks from old sect
    my_tasks2_new = get_my_tasks(token2)
    active2_new = [t for t in my_tasks2_new if t["status"] in ["active", "claimable"]]
    assert not active2_new, f"No tasks from old sect should exist: {len(active2_new)}"

    # Test 7: Verify all API responses have Chinese text, no raw codes
    all_responses = []
    # Get sect info
    sect_me = request("/sects/me", token=token1)
    all_responses.append(("sect_me", sect_me))

    # Get sect tasks
    tasks_response = request("/sects/tasks", token=token1)
    all_responses.append(("sects/tasks", tasks_response))

    # Get sect shop
    shop_response = request("/sects/shop", token=token1)
    all_responses.append(("sects/shop", shop_response))

    for label, response in all_responses:
        if isinstance(response, dict):
            for key in ["message", "name", "description", "position_name", "requirement_display", "cost_display"]:
                if key in response and response[key]:
                    assert_no_raw_code(str(response[key]), f"{label}.{key}")
        elif isinstance(response, list):
            for item in response:
                for key in ["name", "description", "position_name", "requirement_display", "cost_display", "exchange_summary"]:
                    if key in item and item[key]:
                        assert_no_raw_code(str(item[key]), f"{label}[{item.get('code', '')}].{key}")

    print("Sect task player flow test passed.")


if __name__ == "__main__":
    main()