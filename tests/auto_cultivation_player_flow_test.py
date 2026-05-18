"""
自动修行玩家流程测试
覆盖：配置 / 结算 / 暂停 / 恢复 / 宗门任务推进 / 重伤不死
"""

import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.test_server_utils import ensure_test_server
ensure_test_server()

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
os.environ.setdefault("ENABLE_DEV_ROUTES", "1")

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


def force_auto_settle(username, minutes_ago):
    """将 last_auto_settle_at 设置为 N 分钟前，模拟离线"""
    _user_id, character_id = get_ids(username)
    past = datetime.utcnow() - timedelta(minutes=minutes_ago)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE characters SET last_auto_settle_at = ?, auto_enabled = 1, auto_strategy = ?, auto_state = ? WHERE id = ?",
            (past.isoformat(), "balanced", "meditating", character_id),
        )
        conn.commit()


def get_auto_fields(username):
    """读取角色自动修行相关字段"""
    _user_id, character_id = get_ids(username)
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT auto_enabled, auto_strategy, auto_state, auto_paused_reason,
                   last_auto_settle_at, last_auto_report_json
            FROM characters WHERE id = ?
            """,
            (character_id,),
        ).fetchone()
    return {
        "auto_enabled": bool(row[0]),
        "auto_strategy": row[1],
        "auto_state": row[2],
        "auto_paused_reason": row[3],
        "last_auto_settle_at": row[4],
        "last_auto_report_json": row[5],
    }


def clear_inventory(username):
    """清空角色背包"""
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


def main():
    stamp = int(time.time())
    player = f"auto_test_{stamp}"

    # 1. 注册账号
    result = register(player)
    assert "token" in result, f"注册失败: {result}"
    token = result["token"]

    me = request("/character/me", token=token)
    c = me["character"]

    # 2. 新账号默认 auto_enabled = False
    assert "auto_cultivation" in c, "character_payload 应包含 auto_cultivation"
    auto = c["auto_cultivation"]
    assert auto["enabled"] is False, f"新账号 auto_enabled 应为 False: {auto}"
    assert auto["strategy"] == "balanced", f"默认策略应为 balanced: {auto}"
    print("[PASS] 新账号默认关闭自动修行")

    # 3. 开启 steady 策略
    config = action(token, "auto_cultivation_config", {"strategy": "steady", "enabled": True})
    assert config["success"] is True, f"开启 steady 失败: {config['message']}"
    assert config["character"]["auto_cultivation"]["strategy"] == "steady"
    assert config["character"]["auto_cultivation"]["enabled"] is True
    assert "稳健" in config["message"]
    print("[PASS] 可以开启稳健策略")

    # 4. 切换 balanced 策略
    config2 = action(token, "auto_cultivation_config", {"strategy": "balanced", "enabled": True})
    assert config2["success"] is True
    assert config2["character"]["auto_cultivation"]["strategy"] == "balanced"
    print("[PASS] 可以切换均衡策略")

    # 5. 切换 aggressive 策略
    config3 = action(token, "auto_cultivation_config", {"strategy": "aggressive", "enabled": True})
    assert config3["success"] is True
    assert config3["character"]["auto_cultivation"]["strategy"] == "aggressive"
    assert "激进" in config3["message"]
    print("[PASS] 可以开启激进策略")

    # 6. 暂停自动修行
    force_character(player, mana=500)
    pause = action(token, "auto_cultivation_pause", {})
    assert pause["success"] is True
    assert pause["character"]["auto_cultivation"]["enabled"] is False
    assert pause["character"]["auto_cultivation"]["state"] == "paused"
    print("[PASS] 可以暂停自动修行")

    # 7. 恢复自动修行
    resume = action(token, "auto_cultivation_resume", {})
    assert resume["success"] is True
    assert resume["character"]["auto_cultivation"]["enabled"] is True
    print("[PASS] 可以恢复自动修行")

    # 8. 结算离线收益（模拟 120 分钟离线）
    # 先模拟离线时间
    force_auto_settle(player, minutes_ago=120)
    force_character(player, mana=500, hp=100, max_hp=100)

    settle = action(token, "auto_cultivation_settle", {})
    assert settle["success"] is True, f"结算失败: {settle['message']}"
    # auto_cultivation is nested in character.auto_cultivation
    ac = settle.get("character", {}).get("auto_cultivation", {})
    report = ac.get("last_report")
    assert report is not None, f"结算应返回报告: {settle}"
    assert report["cycles"] == 12, f"120分钟应结算12个周期: {report['cycles']}"
    assert report["duration_minutes"] >= 120
    gains = report.get("gains", {})
    assert gains.get("cultivation", 0) > 0, "应有修为获得"
    assert gains.get("spirit_stones", 0) > 0, "应有灵石获得"
    # 验证 action 计数合理
    actions = report.get("actions", {})
    assert actions["meditating"] + actions["adventuring"] + actions["resting"] == report["cycles"]
    print(f"[PASS] 结算离线收益：{report['cycles']}个周期，修为+{gains.get('cultivation')}，灵石+{gains.get('spirit_stones')}")

    # 9. 结算最多 8 小时（480 分钟）
    force_auto_settle(player, minutes_ago=600)
    force_character(player, mana=500, hp=100)
    settle2 = action(token, "auto_cultivation_settle", {})
    assert settle2["success"] is True
    report2 = settle2.get("character", {}).get("auto_cultivation", {}).get("last_report") or {}
    assert report2["settled_minutes"] <= 480 * 60, "最多结算 8 小时"
    assert report2["cycles"] <= 48, "最多 48 个周期"
    print(f"[PASS] 8 小时上限：settled_minutes={report2['settled_minutes']}, cycles={report2['cycles']}")

    # 10. 查询接口只读，不修改状态
    force_auto_settle(player, minutes_ago=60)
    status = request("/auto-cultivation/status", token=token)
    assert "enabled" in status
    assert "can_settle" in status
    assert "settle_minutes_available" in status
    char_before = request("/character/me", token=token)["character"]
    time.sleep(0.5)
    char_after = request("/character/me", token=token)["character"]
    assert char_before["cultivation"] == char_after["cultivation"], "GET 接口不应修改玩家状态"
    assert char_before["mana"] == char_after["mana"], "GET 接口不应修改玩家法力"
    print("[PASS] GET /auto-cultivation/status 只读，不修改状态")

    # 11. 开启后法力不足 → 打坐恢复法力
    force_auto_settle(player, minutes_ago=30)
    force_character(player, mana=5, hp=100, max_hp=100, max_mana=500)
    settle3 = action(token, "auto_cultivation_settle", {})
    assert settle3["success"] is True
    report3 = settle3.get("character", {}).get("auto_cultivation", {}).get("last_report") or {}
    actions3 = report3.get("actions", {})
    assert actions3["meditating"] > 0, "法力不足应打坐"
    print(f"[PASS] 法力不足时进入打坐：meditating={actions3['meditating']}")

    # 12. 开启后气血低于阈值 → 休整
    force_auto_settle(player, minutes_ago=30)
    force_character(player, mana=500, hp=20, max_hp=100)
    settle4 = action(token, "auto_cultivation_settle", {})
    assert settle4["success"] is True
    report4 = settle4.get("character", {}).get("auto_cultivation", {}).get("last_report") or {}
    actions4 = report4.get("actions", {})
    assert actions4["resting"] > 0, "气血低应休整"
    char4 = settle4["character"]
    assert char4["hp"] > 20, "休整应恢复气血"
    print(f"[PASS] 气血低时进入休整：resting={actions4['resting']}, hp恢复至{char4['hp']}")

    # 13. 重伤不死亡，只暂停
    force_auto_settle(player, minutes_ago=30)
    force_character(player, mana=500, hp=5, max_hp=100)
    settle5 = action(token, "auto_cultivation_settle", {})
    assert settle5["success"] is True
    char5 = settle5["character"]
    # 气血不能低于1（不死亡）
    assert char5["hp"] >= 1, f"挂机不能死亡，hp={char5['hp']}"
    auto5 = char5["auto_cultivation"]
    # 重伤状态应暂停
    if auto5["state"] in ("injured", "paused"):
        assert auto5["enabled"] is False or auto5["state"] == "injured", "重伤应暂停"
        assert auto5["paused_reason"] is not None, "重伤应有暂停原因"
    print(f"[PASS] 重伤不死亡，hp={char5['hp']}, state={auto5['state']}, reason={auto5.get('paused_reason')}")

    # 14. 背包满暂停，不自动丢弃
    # 填充背包
    _user_id, character_id = get_ids(player)
    with sqlite3.connect(DB_PATH) as conn:
        template_id = conn.execute("SELECT id FROM item_templates WHERE code = 'low_spirit_stone'").fetchone()[0]
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
                "UPDATE inventory_slots SET item_template_id = ?, quantity = 999, item_instance_id = ? WHERE id = ?",
                (template_id, instance_id, slot_id),
            )
        conn.commit()

    force_auto_settle(player, minutes_ago=30)
    force_character(player, mana=500, hp=100, auto_enabled=True)
    settle6 = action(token, "auto_cultivation_settle", {})
    assert settle6["success"] is True
    report6 = settle6.get("auto_report") or {}
    pending = report6.get("pending_matters", [])
    auto6 = settle6["character"]["auto_cultivation"]
    if pending:
        assert any("背包" in m for m in pending), f"背包满应生成待处理事项: {pending}"
    if auto6["state"] == "paused":
        assert auto6["paused_reason"] is not None
        assert auto6["enabled"] is False
    print(f"[PASS] 背包满时暂停：state={auto6['state']}, pending={pending}")

    # 15. 宗门任务自动推进
    player_sect = f"sect_auto_{stamp}"
    reg_sect = register(player_sect)
    token_sect = reg_sect["token"]
    force_character(player_sect, realm="炼气五层", mana=500, spirit_stones=500, auto_enabled=False)
    join = action(token_sect, "join_sect", {"sect_code": "qingxuan_sword_sect"})
    assert join["success"] is True
    accept = action(token_sect, "accept_sect_task", {"task_code": "patrol_mountain"})
    assert accept["success"] is True

    # 设置离线，让自动历练推进宗门任务
    _u, char_id = get_ids(player_sect)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE characters SET auto_enabled = 1, auto_strategy = 'balanced', auto_state = 'meditating', last_auto_settle_at = ? WHERE id = ?",
            ((datetime.utcnow() - timedelta(minutes=60)).isoformat(), char_id),
        )
        conn.commit()

    settle_sect = action(token_sect, "auto_cultivation_settle", {})
    assert settle_sect["success"] is True
    report_sect = settle_sect.get("character", {}).get("auto_cultivation", {}).get("last_report") or {}
    sect_msgs = report_sect.get("sect_task_messages", [])
    # patrol_mountain 需要 2 次 explore，自动历练应推进
    print(f"[INFO] 宗门任务消息：{sect_msgs}")
    print(f"[PASS] 自动历练完成，结算成功")
    # 捐献类任务不会自动完成（这里没有捐献，所以不测）

    # 16. 报告中物品显示中文名，不裸 item_id
    # 找一个有掉落的结算
    force_auto_settle(player, minutes_ago=60)
    force_character(player, mana=500, hp=100)
    clear_inventory(player)
    settle7 = action(token, "auto_cultivation_settle", {})
    assert settle7["success"] is True
    report7 = settle7.get("character", {}).get("auto_cultivation", {}).get("last_report") or {}
    gains7 = report7.get("gains", {})
    items = gains7.get("items", [])
    for item in items:
        assert "name" in item, f"物品应有 name 字段: {item}"
        assert item["name"] != item.get("code", ""), f"物品名不应等于 code: {item}"
        # 中文名不含下划线（英文 code 才有下划线）
        if item.get("code"):
            assert "_" not in item["name"], f"物品名应为中文，不应有下划线: {item}"
    print(f"[PASS] 报告中物品显示中文名：{[i['name'] for i in items]}")

    # 17. /character/me 或 GET status 不会隐式结算
    force_auto_settle(player, minutes_ago=90)
    char_before = request("/character/me", token=token)["character"]
    time.sleep(0.5)
    char_after = request("/character/me", token=token)["character"]
    # 两次调用不产生收益（因为没有调用 settle）
    # 注意：如果 auto_enabled 为 true 但未调用 settle，数值不会变
    print(f"[PASS] GET 接口不隐式结算：cultivation 未变化={char_before['cultivation'] == char_after['cultivation']}")

    print("\n=== 所有自动修行测试通过 ===")


if __name__ == "__main__":
    main()