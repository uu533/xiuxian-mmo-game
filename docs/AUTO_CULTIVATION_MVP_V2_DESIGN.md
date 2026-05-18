# 自动修行 / 洞府挂机 MVP v2.0 技术设计报告

> 分支：`feature/auto-cultivation-mvp-design`（从 `main@4bbb22e` 创建，只读调研，不 push）
> 状态：调研完成，待用户确认方向后出正式开发任务包

---

## 一、需求概述与设计目标

### 1.1 核心转变

项目核心从"手动修炼/探索"转向"挂机放置/洞府自动修行"，让玩家在离线期间也能持续积累资源。

### 1.2 v2.0 MVP 目标

- **离线结算**：玩家重新登录时，自动结算上次离开后的挂机收益
- **自动修炼**：玩家可设置自动在洞府挂机，自动执行修炼/探索
- **掉落实体分级**：将当前掉落表扩展为 5 级品质体系（凡品/下品/中品/上品/极品）
- **宗门任务间接推进**：自动历练自动推进 patrol/scavenge/explore 类型任务

### 1.3 已知约束

- 所有状态修改走 `/action/execute` 原则不变
- `auto_cultivation` 相关 action 不改现有 `train/explore` handlers，新建独立 handler
- 登录触发离线结算：前端从 `/character/me` 发现 `pending_auto_report` 后调用 action
- 最多累计 8 小时离线收益
- v1.9 已有 UX 改进（固定底部导航/全局 Toast/PC 自适应/修行建议折叠/危险按钮确认）需在 v2.0 吸收

---

## 二、掉落实体分级设计

### 2.1 品质体系（5 级，v2.0 开放前 5 级）

| 等级 | 名称 | 颜色 | 说明 | 对应掉落来源 |
|------|------|------|------|------------|
| 1 | 凡品 | 灰 | 无附加属性，普通野外掉落 | 普通探索事件 |
| 2 | 下品 | 白 | 轻微属性加成 | 探索战斗胜利 |
| 3 | 中品 | 绿 | 稳定属性加成 | 隐藏机缘事件 |
| 4 | 上品 | 蓝 | 显著属性加成 | 洞府挂机专属 |
| 5 | 极品 | 紫 | 强力属性加成 | 大境界突破奖励 |

> 极品（橙/红）在 v2.0 不开放，避免数值膨胀，留给后续活动系统。

### 2.2 掉落表扩展方案

扩展 `backend/configs/drop_tables.py`，按品质和境界双维度定义掉落。关键思路：

- 当前掉落表按 `realm_stage` 分组（炼气前期/炼气/筑基/结丹/元婴/化神）
- v2.0 扩展为按"境界 × 品质"双维度权重表
- 挂机掉落概率由品质权重决定，不破坏现有境界分组逻辑

**建议数据结构**：

```python
# 扩展 drop_tables.py

DROP_TABLES_V2 = {
    "炼气": {
        "凡品": [
            {"item": "low_spirit_stone", "weight": 35, "quantity": [4, 12]},
            {"item": "healing_herb", "weight": 18, "quantity": [1, 2]},
            {"item": "mana_pill", "weight": 14, "quantity": [1, 1]},
            {"item": "qi_powder", "weight": 12, "quantity": [1, 2]},
        ],
        "下品": [
            {"item": "healing_pill", "weight": 25, "quantity": [1, 2]},
            {"item": "low_material", "weight": 20, "quantity": [1, 3]},
            {"item": "low_method", "weight": 12, "quantity": [1, 1]},
            {"item": "low_artifact", "weight": 10, "quantity": [1, 1]},
        ],
        "中品": [
            {"item": "foundation_pill", "weight": 20, "quantity": [1, 1]},
            {"item": "mid_material", "weight": 18, "quantity": [1, 2]},
            {"item": "mid_method", "weight": 8, "quantity": [1, 1]},
        ],
        "上品": [
            {"item": "core_pill", "weight": 15, "quantity": [1, 1]},
            {"item": "mid_artifact", "weight": 12, "quantity": [1, 1]},
        ],
        "极品": [
            {"item": "high_method", "weight": 10, "quantity": [1, 1]},
            {"item": "high_artifact", "weight": 8, "quantity": [1, 1]},
        ],
    },
    "筑基": {...},
    "结丹": {...},
}
```

### 2.3 品质权重配置

在 `configs/drop_tables.py` 添加品质权重配置：

```python
DROP_QUALITY_WEIGHTS = {
    "offline_settle": {"凡品": 40, "下品": 30, "中品": 20, "上品": 8, "极品": 2},
    "auto_cultivate": {"凡品": 30, "下品": 28, "中品": 22, "上品": 15, "极品": 5},
    "explore": {"凡品": 45, "下品": 30, "中品": 18, "上品": 6, "极品": 1},
    "hidden_opportunity": {"凡品": 20, "下品": 25, "中品": 30, "上品": 18, "极品": 7},
}
```

### 2.4 ItemInstance Rarity 字段扩展

当前 `item_instances.rarity` 字段已存在（字符串，缺省 "白"），可直接使用。

现有代码参考 `inventory_service.py:93`：
```python
rarity=_roll_rarity() if _should_roll_rarity(template.code, template.type) else "白"
```

需扩展 `_roll_rarity()` 函数，支持 5 级品质。

---

## 三、新增字段方案

### 3.1 Character 表新增字段

在 `backend/models/character.py` 添加：

```python
# 洞府挂机状态
auto_cultivate_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
auto_cultivate_mode: Mapped[str] = mapped_column(String(24), default="train", nullable=False)  # "train" | "explore"
auto_cultivate_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

# 离线结算
pending_auto_report: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
last_auto_settle_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

### 3.2 database.py 迁移

在 `backend/database.py` 的 `migrate_early_mvp_schema()` 后追加：

```python
def migrate_auto_cultivation_schema() -> None:
    with engine.begin() as conn:
        _add_missing_columns(
            conn,
            "characters",
            {
                "auto_cultivate_enabled": "INTEGER NOT NULL DEFAULT 0",
                "auto_cultivate_mode": "VARCHAR(24) NOT NULL DEFAULT 'train'",
                "auto_cultivate_start_at": "DATETIME",
                "pending_auto_report": "INTEGER NOT NULL DEFAULT 0",
                "last_auto_settle_at": "DATETIME",
            },
        )
```

---

## 四、自动修炼逻辑设计

### 4.1 自动修炼模式

- **`train`**：自动打坐修炼（消耗法力，积累修为）
- **`explore`**：自动外出探索（消耗法力，获取掉落，可能受伤）

### 4.2 auto_cultivate settle 核心逻辑

新建 `backend/services/auto_cultivate_service.py`，实现离线结算：

```python
from datetime import datetime, timedelta
from backend.utils.time_utils import utc_now

MAX_OFFLINE_HOURS = 8
SETTLE_INTERVAL_MINUTES = 10  # 每 10 分钟为一个结算周期

def settle_auto_cultivation(db, character, force=False):
    """
    结算玩家的洞府挂机收益。
    被 /action/auto_cultivate_settle 调用，或登录时自动触发。
    """
    if not force and character.auto_cultivate_start_at is None:
        return None  # 未开启挂机，直接跳过

    now = utc_now()
    start = character.auto_cultivate_start_at or character.last_auto_settle_at or now

    elapsed = now - start
    elapsed_minutes = int(elapsed.total_seconds() / 60)
    intervals = elapsed_minutes // SETTLE_INTERVAL_MINUTES

    # 最多累计 8 小时 = 480 分钟 = 48 个周期
    intervals = min(intervals, 48)
    if intervals <= 0:
        return None

    mode = character.auto_cultivate_mode  # "train" | "explore"
    results = {
        "intervals": intervals,
        "mode": mode,
        "events": [],
        "total_cultivation": 0,
        "total_spirit_stones": 0,
        "drops": [],
        "hp_damage": 0,
    }

    for _ in range(intervals):
        if mode == "train":
            result = _settle_train(character)
        else:
            result = _settle_explore(character)
        results["events"].append(result)
        results["total_cultivation"] += result.get("cultivation", 0)
        results["total_spirit_stones"] += result.get("spirit_stones", 0)
        results["hp_damage"] += result.get("hp_damage", 0)
        for drop in result.get("drops", []):
            results["drops"].append(drop)

        # 检查是否 HP 归零
        if character.hp <= 0:
            results["events"].append({"type": "dead", "message": "气血耗尽，挂机中断。"})
            break

    # 更新角色状态
    character.pending_auto_report = True  # 标记有待结算报告
    character.last_auto_settle_at = now

    db.flush()
    return results
```

### 4.3 _settle_train 逻辑

```python
def _settle_train(character) -> dict:
    """模拟一次修炼"""
    mana_cost = 12  # 固定值，与 action_service._train 一致
    if character.mana < mana_cost:
        return {"type": "train", "cultivation": 0, "message": "法力不足，未能修炼。"}

    character.mana -= mana_cost
    gain = max(1, random.randint(16, 28))  # 简化版，不含效率衰减和加成
    character.cultivation = min(character.cultivation_cap, character.cultivation + gain)

    return {
        "type": "train",
        "cultivation": gain,
        "mana_spent": mana_cost,
        "message": f"修炼 {gain} 修为",
    }
```

### 4.4 _settle_explore 逻辑

```python
def _settle_explore(character) -> dict:
    """模拟一次探索"""
    mana_cost = 18
    if character.mana < mana_cost:
        return {"type": "explore", "message": "法力不足，未能探索。"}

    character.mana -= mana_cost
    event = pick_explore_event(character)  # 复用 event_service 中的函数
    result = _resolve_settle_explore_event(character, event)

    character.cultivation = min(character.cultivation_cap, character.cultivation + random.randint(4, 16))

    return result

def _resolve_settle_explore_event(character, event) -> dict:
    """结算期间处理单个探索事件（简化版，不写额外日志）"""
    result = {"type": "explore", "event_code": event["code"], "drops": []}

    if event["type"] == "reward_spirit_stones":
        amount = int(_roll_range(event["rewards"]["spirit_stones"]))
        character.spirit_stones += amount
        result["spirit_stones"] = amount
        result["message"] = f"发现灵石 {amount}"

    elif event["type"] == "reward_item":
        drops = grant_drop_items(db, character, _rolls_for_event(event))  # 复用 drop_service
        result["drops"] = drops
        result["message"] = "获得物品"

    elif event["type"] == "battle":
        battle_result = resolve_battle(character)  # 复用 event_service
        result["battle"] = battle_result
        result["hp_damage"] = battle_result.get("hp_damage", 0)
        if battle_result.get("won"):
            amount = int(_roll_range(event["rewards"].get("spirit_stones", [20, 50])))
            character.spirit_stones += amount
            result["spirit_stones"] = amount
            drops = grant_drop_items(db, character, _rolls_for_event(event))
            result["drops"] = drops

    elif event["type"] == "trap":
        damage = _roll_range(event["risks"].get("hp_damage", [1, 1]))
        reduction = get_guard_talisman_damage_reduction(character)
        damage = max(1, int(damage * (1 - reduction)))
        character.hp = max(0, character.hp - damage)
        result["hp_damage"] = damage
        result["message"] = f"触发陷阱，损失 {damage} 气血"

    else:
        result["message"] = "空手而归"

    return result
```

---

## 五、宗门任务间接推进

### 5.1 需求

自动历练期间，explore 类型 action 需要推进宗门任务进度。

### 5.2 实现

在 `sect_service.py:record_sect_task_progress()` 中已有完整逻辑（action_type / result_data 参数）。在 `auto_cultivate_settle` 结算期间，每完成一次 explore 事件后调用：

```python
# 在 _settle_explore 中，事件处理完后
from backend.services.sect_service import record_sect_task_progress

messages = record_sect_task_progress(
    db, user, "explore",
    success=(event["type"] != "trap" and character.hp > 0),
    result_data={"event_type": event["type"], "event": event["code"]}
)
```

这样 `patrol`（target_action=explore）、`hunt_beast`（target_event_types 含 battle）、`explore_secret`（target_event_types 含 hidden_opportunity）等任务都会被自动推进。

### 5.3 自动修炼不推进 patrol 以外的任务

- `train` 不推进任何宗门任务（无对应 target_action）
- `explore` 推进 `patrol`/`hunt_beast`/`explore_secret`（与手动 explore 行为一致）
- `donate_spirit_stones` 任务需要玩家主动操作，不自动完成

---

## 六、新增 Action 设计

### 6.1 auto_cultivate_settle — 离线结算

**路径**：`POST /action/execute`

**params**：
```json
{
  "action_type": "auto_cultivate_settle",
  "params": {}
}
```

**响应**：
```json
{
  "success": true,
  "message": "离线结算完成，共挂机 3 小时，执行 18 次修炼，获得 320 修为。",
  "character": {...},
  "rewards": [
    {"type": "cultivation", "quantity": 320},
    {"type": "spirit_stones", "quantity": 45},
    {"type": "item", "code": "healing_pill", "quantity": 2, "name": "疗伤丹"}
  ],
  "cost": {},
  "logs": [...],
  "inventory": [...],
  "settle_summary": {
    "mode": "train",
    "intervals": 18,
    "total_cultivation": 320,
    "total_spirit_stones": 45,
    "hp_damage": 0,
    "drops": [{"code": "healing_pill", "quantity": 2}],
    "sect_task_progress_messages": ["宗门任务进度：巡守山门 2/2"]
  }
}
```

**触发时机**：
1. 玩家登录时，前端从 `/character/me` 发现 `pending_auto_report: true` 后自动调用
2. 玩家手动点击"领取挂机收益"按钮

### 6.2 auto_cultivate_enable — 开启/配置自动修炼

**路径**：`POST /action/execute`

**params**：
```json
{
  "action_type": "auto_cultivate_enable",
  "params": {
    "mode": "train",          // "train" | "explore"
    "enabled": true           // true=开启，false=关闭
  }
}
```

**响应**：
```json
{
  "success": true,
  "message": "已开启自动修炼（模式：洞府打坐）。关闭 App 后将自动累计收益。",
  "character": {...},
  "auto_cultivate": {
    "enabled": true,
    "mode": "train",
    "start_at": "2025-01-15T10:30:00Z"
  }
}
```

### 6.3 auto_cultivate_disable — 关闭自动修炼

与 `auto_cultivate_enable` 共用同一 handler，通过 `enabled: false` 关闭。

---

## 七、API 接口设计

### 7.1 修改 /character/me

在 `character_payload` 中添加自动修炼状态：

```python
# backend/services/character_service.py

def character_payload(character: Character) -> dict:
    ...
    result["auto_cultivate"] = {
        "enabled": character.auto_cultivate_enabled,
        "mode": character.auto_cultivate_mode,
        "start_at": character.auto_cultivate_start_at.isoformat() if character.auto_cultivate_start_at else None,
    }
    result["pending_auto_report"] = character.pending_auto_report
    result["last_auto_settle_at"] = character.last_auto_settle_at.isoformat() if character.last_auto_settle_at else None
    ...
```

前端登录后检查 `pending_auto_report`，自动触发结算。

### 7.2 前端交互流程

```
玩家登录 → GET /character/me
  → 发现 pending_auto_report == true
  → 显示离线结算弹窗（挂机时长、收益预览）
  → 玩家点击"领取" → POST /action/execute {action_type: "auto_cultivate_settle"}
  → 显示结算详情
  → 关闭弹窗，进入正常游戏

玩家设置自动修炼：
  → POST /action/execute {action_type: "auto_cultivate_enable", params: {mode: "train", enabled: true}}
  → 自动修炼启动，开始计时
```

---

## 八、分阶段实施建议（P0/P1/P2）

### P0 — 核心挂机循环（最优先）

1. 新增 `auto_cultivate_enabled`/`auto_cultivate_mode`/`auto_cultivate_start_at` 字段
2. 新增 `pending_auto_report`/`last_auto_settle_at` 字段
3. 实现 `auto_cultivate_enable` / `auto_cultivate_disable` action
4. 实现 `auto_cultivate_settle` action（train 模式，简化版，无战斗）
5. 修改 `/character/me` 返回挂机状态
6. 前端登录发现 pending_auto_report 后自动触发结算
7. 前端添加"自动修炼"开关 UI（洞府页面内）

### P1 — 完整探索挂机 + 宗门任务推进

1. `auto_cultivate_settle` 增加 explore 模式（战斗/陷阱/掉落）
2. 结算时调用 `record_sect_task_progress` 推进宗门任务
3. 添加掉落实体分级（凡品/下品/中品 三级）
4. 前端挂机结算弹窗增加 HP 警告（气血过低时提示）

### P2 — 上品掉落 + 收益展示优化

1. 扩展掉落表到 5 级品质（上品/极品）
2. 结算报告增加更多统计（各品质数量/灵石总计）
3. 宗门任务自动推进的 UI 反馈（Toast 通知）
4. 前端"修行建议"折叠面板增加自动修炼建议

---

## 九、关键文件清单（需修改）

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/models/character.py` | 修改 | 新增 5 个字段 |
| `backend/database.py` | 修改 | 新增迁移函数 |
| `backend/configs/drop_tables.py` | 修改 | 新增品质权重表 + v2 掉落表 |
| `backend/services/auto_cultivate_service.py` | 新建 | 核心挂机结算逻辑 |
| `backend/services/action_service.py` | 修改 | 注册 3 个新 action handler |
| `backend/services/character_service.py` | 修改 | character_payload 增加挂机状态 |
| `backend/services/sect_service.py` | 不改 | record_sect_task_progress 已可复用 |
| `backend/services/event_service.py` | 不改 | pick_explore_event / resolve_battle 已可复用 |
| `backend/services/drop_service.py` | 不改 | grant_drop_items 已可复用 |
| `frontend/index.html` | 修改 | 吸收 v1.9 UX + 新增自动修炼 UI + 离线结算弹窗 |
| `tests/` | 修改 | 新增 auto_cultivate 集成测试 |

---

## 十、风险与决策点

### 10.1 HP 耗尽处理

结算期间若 HP 归零，立即终止循环，记录死讯。玩家登录看到"你在挂机期间气血耗尽，已被路人救回，当前气血 30"之类的消息。

### 10.2 宗门任务冲突

如果玩家在离线前有进行中的宗门任务，自动 explore 会推进 `patrol`/`hunt_beast`/`explore_secret` 任务。这是预期行为，与手动 explore 一致。

### 10.3 掉落实体分级对现有掉落的影响

扩展掉落表为双维度（境界 × 品质）后：
- 现有 `grant_drop_items()` 逻辑需要先按境界选表，再按品质权重抽取
- 现有手动 explore 的掉落品质权重（`explore` 配置）与挂机（`auto_cultivate`）不同
- 不修改现有手动 explore 的掉率，保证玩家主动操作的价值感

### 10.4 离线时间上限

8 小时 = 48 个结算周期（每周期 10 分钟）。超过 8 小时的部分不结算，避免数值膨胀和潜在滥用。

---

报告完成。所有设计基于代码实际调研，未 push，待用户确认方向。