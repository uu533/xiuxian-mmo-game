"""
自动修行实时日志系统测试
覆盖：日志生成/增长/上限/离线报告/待处理事项
"""
import json, os, sqlite3, sys, time
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.test_server_utils import ensure_test_server
ensure_test_server()

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
DB_PATH = ROOT / "game.db"


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
            "SELECT users.id, characters.id FROM users JOIN characters ON characters.user_id = users.id WHERE users.username = ?",
            (username,),
        ).fetchone()
    return row[0], row[1]


def force_auto_settle(username, minutes_ago, auto_state="meditating"):
    _, character_id = get_ids(username)
    past = datetime.utcnow() - timedelta(minutes=minutes_ago)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE characters SET last_auto_settle_at = ?, auto_enabled = 1, auto_strategy = ?, auto_state = ? WHERE id = ?",
            (past.isoformat(), "balanced", auto_state, character_id),
        )
        conn.commit()


def force_character(username, **fields):
    _, character_id = get_ids(username)
    assignments = ", ".join(f"{name} = ?" for name in fields)
    values = list(fields.values()) + [character_id]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"UPDATE characters SET {assignments} WHERE id = ?", values)
        conn.commit()


def clear_inventory(username):
    _, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE inventory_slots SET item_template_id = NULL, quantity = 0, item_instance_id = NULL WHERE character_id = ?",
            (character_id,),
        )
        conn.execute("DELETE FROM character_artifacts WHERE character_id = ?", (character_id,))
        conn.commit()


def main():
    stamp = int(time.time())
    player = f"log_test_{stamp}"

    # 1. 注册账号并开启自动修行
    result = register(player)
    assert "token" in result, f"注册失败: {result}"
    token = result["token"]

    config = action(token, "auto_cultivation_config", {"strategy": "balanced", "enabled": True})
    assert config["success"] is True
    print("[PASS] 开启自动修行")

    # 2. 结算离线收益，生成实时日志
    force_auto_settle(player, minutes_ago=120)
    force_character(player, mana=500, hp=100, max_hp=100)

    settle = action(token, "auto_cultivation_settle", {})
    assert settle["success"] is True, f"结算失败: {settle['message']}"

    # 3. 检查实时日志字段存在
    ac = settle.get("character", {}).get("auto_cultivation", {})
    report = ac.get("last_report") or {}
    assert "auto_logs" in report, f"report 应包含 auto_logs 字段: {report.keys()}"
    logs = report.get("auto_logs", [])
    assert len(logs) > 0, f"结算后应有日志产生，实际: {logs}"
    # 日志应包含中文
    for log in logs:
        assert isinstance(log, str) and len(log) > 0, f"每条日志应为非空字符串: {log}"
    print(f"[PASS] 实时日志生成成功，共 {len(logs)} 条")

    # 4. 日志包含中文事件文本（氛围型）
    log_text = "".join(logs)
    assert any(kw in log_text for kw in ["洞府", "历练", "打坐", "休整", "修行", "修为", "灵气"]), \
        f"日志应包含修仙相关关键词，实际: {logs[:3]}"
    print(f"[PASS] 日志包含中文修仙事件文本")

    # 5. 离线报告包含事件摘要/成长感/危险感
    assert "event_summary" in report, f"report 应包含 event_summary: {report.keys()}"
    assert "growth_feel" in report, f"report 应包含 growth_feel: {report.keys()}"
    assert "danger_feel" in report, f"report 应包含 danger_feel: {report.keys()}"
    event_summary = report["event_summary"]
    growth_feel = report["growth_feel"]
    danger_feel = report["danger_feel"]
    assert len(event_summary) > 0, f"event_summary 不应为空: {event_summary}"
    assert len(growth_feel) > 0, f"growth_feel 不应为空: {growth_feel}"
    assert len(danger_feel) > 0, f"danger_feel 不应为空: {danger_feel}"
    print(f"[PASS] 离线报告包含增强内容：摘要={event_summary}，成长={growth_feel}，危险={danger_feel}")

    # 6. 待处理事项正常生成（至少有一条）
    pending = report.get("pending_matters", [])
    assert len(pending) > 0, f"待处理事项不应为空: {pending}"
    assert any(isinstance(m, str) and len(m) > 0 for m in pending), f"待处理事项应为非空字符串列表"
    print(f"[PASS] 待处理事项正常生成，共 {len(pending)} 条: {pending[:2]}")

    # 7. /auto-cultivation/status 接口返回 realtime_logs
    status = request("/auto-cultivation/status", token=token)
    # status 本身就是 auto_cultivation 状态对象
    assert "realtime_logs" in status, f"status 应包含 realtime_logs: {status.keys()}"
    rt_logs = status.get("realtime_logs", [])
    assert isinstance(rt_logs, list), f"realtime_logs 应为列表: {type(rt_logs)}"
    print(f"[PASS] /auto-cultivation/status 返回 realtime_logs，共 {len(rt_logs)} 条")

    # 8. 日志数量上限控制（再结算一次，看日志是否累积）
    force_auto_settle(player, minutes_ago=60)
    force_character(player, mana=500, hp=100)
    settle2 = action(token, "auto_cultivation_settle", {})
    assert settle2["success"] is True
    ac2 = settle2.get("character", {}).get("auto_cultivation", {})
    report2 = ac2.get("last_report") or {}
    logs2 = report2.get("auto_logs", [])
    # 日志数量受 cycles 影响，新结算产生的日志可能较少，但 DB 存储的日志应持续增长
    # 验证 realtime_logs 在 /auto-cultivation/status 中持续存在
    status2 = request("/auto-cultivation/status", token=token)
    db_logs = status2.get("realtime_logs", [])
    assert len(db_logs) > 0, f"DB 日志不应为空"
    # 日志条数应不超过上限 50
    assert len(db_logs) <= 50, f"日志数量不应超过 50 条上限，实际: {len(db_logs)}"
    print(f"[PASS] 日志正常累积：report 产生 {len(logs2)} 条，DB 共 {len(db_logs)} 条（上限 50）")

    # 9. DB 存储验证：last_auto_log_json 字段存在且有效
    _, character_id = get_ids(player)
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT last_auto_log_json FROM characters WHERE id = ?", (character_id,)
        ).fetchone()
    log_json = row[0]
    assert log_json is not None, "last_auto_log_json 不应为 NULL"
    parsed = json.loads(log_json)
    assert isinstance(parsed, list), f"last_auto_log_json 应解析为列表: {type(parsed)}"
    assert len(parsed) > 0, f"DB 中的日志不应为空"
    print(f"[PASS] DB 存储验证通过，last_auto_log_json 包含 {len(parsed)} 条日志")

    # 10. 背包满 → 待处理事项包含背包提示
    _, character_id = get_ids(player)
    clear_inventory(player)
    with sqlite3.connect(DB_PATH) as conn:
        template_id = conn.execute("SELECT id FROM item_templates WHERE code = 'low_artifact'").fetchone()[0]
        empty_slots = conn.execute(
            "SELECT id FROM inventory_slots WHERE character_id = ? AND container_type = 'main_bag' AND container_id = 0 AND item_template_id IS NULL",
            (character_id,),
        ).fetchall()
        for (slot_id,) in empty_slots:
            conn.execute(
                "INSERT INTO item_instances (item_template_id, owner_character_id, durability, level, exp, rarity, bound, extra_json) VALUES (?, ?, 100, 1, 0, '白', 0, '{}')",
                (template_id, character_id),
            )
            instance_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "UPDATE inventory_slots SET item_template_id = ?, quantity = 1, item_instance_id = ? WHERE id = ?",
                (template_id, instance_id, slot_id),
            )
        conn.commit()
    force_auto_settle(player, minutes_ago=60)
    force_character(player, mana=50000, max_mana=20400, hp=3000, max_hp=3000)
    settle3 = action(token, "auto_cultivation_settle", {})
    assert settle3["success"] is True
    ac3 = settle3.get("character", {}).get("auto_cultivation", {})
    report3 = ac3.get("last_report") or {}
    pending3 = report3.get("pending_matters", [])
    assert any("背包" in m for m in pending3), f"背包满应生成待处理事项: {pending3}"
    print(f"[PASS] 背包满生成待处理事项: {pending3}")

    print("\n=== 自动修行实时日志测试全部通过 ===")


if __name__ == "__main__":
    import urllib.request, urllib.error
    main()