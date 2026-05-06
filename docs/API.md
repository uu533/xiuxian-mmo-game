# API 设计

默认后端地址：

```text
http://127.0.0.1:8000
```

除注册和登录外，其他接口都需要：

```http
Authorization: Bearer <token>
```

## Auth

### POST /register

```json
{
  "username": "player01",
  "password": "123456"
}
```

```json
{
  "token": "token...",
  "username": "player01"
}
```

### POST /login

```json
{
  "username": "player01",
  "password": "123456"
}
```

```json
{
  "token": "token...",
  "username": "player01"
}
```

## Character

### GET /character/me

返回角色和 81 格主背包。普通接口不暴露 `hidden_luck` 和 `hidden_inner_demon`。

```json
{
  "username": "player01",
  "character": {
    "id": 1,
    "name": "player01",
    "title": "师兄",
    "unlocked_titles": ["师兄", "师姐"],
    "life_status": "存活",
    "realm": "炼气一层",
    "realm_stage": "炼气",
    "cultivation": 0,
    "cultivation_cap": 80,
    "spiritual_root": "水属性天灵根",
    "age": 16,
    "lifespan": 100,
    "hp": 100,
    "max_hp": 110,
    "mana": 100,
    "max_mana": 100,
    "attack": 5,
    "defense": 5,
    "base_attack": 5,
    "base_defense": 5,
    "attack_bonus": 0,
    "defense_bonus": 0,
    "cultivation_speed": 1.45,
    "breakthrough_rate": 0.88,
    "spirit_stones": 100,
    "sect_id": null,
    "sect_name": null,
    "sect_position": "散修",
    "identity_status": "散修"
  },
  "inventory": [],
  "active_task": {
    "id": "task_001",
    "name": "初入修行",
    "description": "完成 5 次修炼，熟悉吐纳节奏。",
    "progress": 0,
    "target": 5,
    "status": "active"
  },
  "tasks": []
}
```

兼容旧路径：`GET /me`。

### POST /character/title

```json
{
  "title": "师姐"
}
```

## Action

### POST /action/execute

统一行为入口。

```json
{
  "action_type": "train",
  "params": {}
}
```

统一返回：

```json
{
  "success": true,
  "message": "打坐修炼消耗 12 点法力，炼化灵气，修为增加 26。",
  "character": {},
  "rewards": [
    {
      "type": "cultivation",
      "quantity": 26
    }
  ],
  "cost": {
    "mana": 12
  },
  "logs": ["打坐修炼消耗 12 点法力，炼化灵气，修为增加 26。"],
  "inventory": []
}
```

支持：

- `train`：修炼，消耗法力，增加修为。
- `explore`：探索，消耗法力，触发配置化事件。
- `breakthrough`：突破，消耗法力，根据修为、境界、隐藏气运和隐藏心魔计算成功率。
- `recover_mana_meditate`：打坐恢复法力。
- `recover_mana_stone`：消耗灵石恢复法力。
- `use_item`：使用背包物品，需要 `params.slot_index`。
- `learn_method`：学习背包中的功法，需要 `params.slot_index`。
- `equip_method`：装备主修功法，需要 `params.method_id`。
- `practice_method`：修炼主修功法，可传 `params.method_id`。
- `equip_artifact`：装备背包中的法宝，需要 `params.slot_index`。
- `unequip_artifact`：卸下法宝，需要 `params.artifact_id`。
- `upgrade_artifact`：强化法宝，需要 `params.artifact_id`。
- `join_sect`：加入宗门，需要 `params.sect_code`。
- `leave_sect`：退出当前宗门。
- `accept_sect_task`：接取宗门任务，需要 `params.task_code`。
- `complete_sect_task`：完成已接宗门任务，可传 `params.task_id`。
- `promote_sect_position`：尝试晋升宗门职位。
- `exchange_sect_reward`：兑换宗门奖励，需要 `params.reward_code`。

示例：学习功法

```json
{
  "action_type": "learn_method",
  "params": {
    "slot_index": 3
  }
}
```

示例：强化法宝

```json
{
  "action_type": "upgrade_artifact",
  "params": {
    "artifact_id": 1
  }
}
```

突破到筑基、结丹、元婴等关键境界时，会检查 `configs/breakthrough_requirements.py` 中的瓶颈条件。例如筑基需要筑基丹、最低法力和主修功法等级。条件不足会返回失败消息，例如：

```json
{
  "success": false,
  "message": "缺少筑基丹"
}
```

兼容旧路径：

- `POST /action/train`
- `POST /action/explore`
- `POST /action/breakthrough`
- `POST /action/meditate`
- `POST /action/spirit-stone`
- `POST /action/pill`

## Inventory

### GET /inventory

返回主背包 81 个固定格子。

```json
[
  {
    "slot_index": 1,
    "container_type": "main_bag",
    "container_id": 0,
    "item_template_id": null,
    "item_instance_id": null,
    "code": null,
    "name": null,
    "type": null,
    "grade": null,
    "quantity": 0,
    "stackable": true
  }
]
```

## Methods

### GET /methods

返回角色已学习功法。

```json
[
  {
    "id": 1,
    "method_code": "low_method",
    "name": "长春功",
    "level": 3,
    "exp": 20,
    "next_exp": 240,
    "equipped": true,
    "effects": {
      "cultivation_speed": 0.04,
      "max_mana": 12,
      "breakthrough_rate": 0.01
    }
  }
]
```

## Artifacts

### GET /artifacts

返回已装备法宝。

```json
[
  {
    "id": 1,
    "slot_type": "main",
    "equipped": true,
    "code": "low_artifact",
    "name": "青锋剑",
    "level": 2,
    "rarity": "白",
    "effects": {
      "attack": 8,
      "defense": 5,
      "explore_reward_bonus": 0.02
    }
  }
]
```

## Drop And Lucky Events

探索事件现在会调用 `configs/drop_tables.py`，按角色境界阶段抽取掉落。掉落会进入 `inventory_slots`。低概率机缘由 `configs/opportunities.py` 控制，可能触发顿悟破境、稀有物品、高人指点、隐秘洞府等事件，并写入 `game_logs` 的 `lucky/drop` 类型日志。

## Sects

宗门配置位于 `backend/configs/sects.py`。当前初始化 8 个 NPC 宗门：

- 正道：青玄剑宗、太清丹阁
- 魔道：血煞门、阴罗教
- 鬼道：幽冥谷、白骨观
- 佛道：金莲寺、大觉禅院

### GET /sects

返回所有 NPC 宗门及加入要求。

### GET /sects/me

返回当前角色宗门、职位、贡献和阵营声望摘要。

### GET /sects/tasks

返回当前宗门和职位可接取的任务。

### GET /sects/tasks/me

返回当前角色已接取/已完成的宗门任务。

### GET /sects/shop

返回当前宗门贡献商店。

加入宗门示例：

```json
{
  "action_type": "join_sect",
  "params": {
    "sect_code": "qingxuan_sword_sect"
  }
}
```

完成任务示例：

```json
{
  "action_type": "complete_sect_task",
  "params": {}
}
```

宗门任务完成后会增加贡献、写入 `game_logs` 的 `sect` 类型日志、写入 `action_records`，并通过 `sect_reputation_logs` 记录阵营声望变化。

## Tasks

新手任务由 `configs/tasks.py` 配置。角色创建或旧角色启动迁移时会自动获得任务，当前版本包含：

- 修炼次数
- 探索次数
- 学习功法
- 装备法宝
- 突破境界

任务进度由后端在行为成功后自动推进，完成后自动发放奖励并写入 `game_logs` 的 `task` 类型日志。前端只展示 `GET /character/me` 返回的 `active_task`。

## Logs

### GET /logs

```json
[
  {
    "id": 1,
    "type": "explore",
    "content": "外出探索消耗 18 点法力。你发现一处废弃矿脉，获得 42 灵石。",
    "data_json": {
      "success": true,
      "event": "spirit_stone_cache",
      "rewards": [
        {
          "type": "spirit_stones",
          "quantity": 42
        }
      ]
    },
    "created_at": "2026-05-05T11:00:00"
  }
]
```

## Dev

### GET /dev/health

```json
{
  "ok": true,
  "message": "Xiuxian MMO API is healthy"
}
```

### GET /dev/db-summary

返回数据库路径、表列表和主要表数据量。仅用于开发期检查。

### GET /dev/simulation

运行自动玩家数值模拟，并把最近一次结果写入项目根目录 `simulation_result.json`。

```text
GET /dev/simulation?hours=3
GET /dev/simulation?hours=3&with_sect=true
```

返回示例：

```json
{
  "time": "3h",
  "realm": "炼气十层",
  "cultivation": 61,
  "cultivation_cap": 1420,
  "progress_ratio": 0.043,
  "spirit_stones": 100,
  "items": {},
  "method_level": 0,
  "artifact_level": 0,
  "breakthrough_attempts": 10,
  "success_rate": 0.9,
  "drop_stats": {},
  "action_counts": {
    "train": 152,
    "breakthrough": 10,
    "recover_mana_meditate": 18
  },
  "average_spirit_stones_per_hour": 0,
  "average_cultivation_per_hour": 1416,
  "mana_blocked_ratio": 0.1,
  "bag_fill_ratio_peak": 0,
  "bottleneck_reasons": {},
  "warnings": [
    "严格修炼策略 1 小时内没有探索收益，前期需要任务引导"
  ],
  "with_sect": false,
  "sect_joined": false,
  "sect_tasks_completed": 0,
  "sect_contribution": 0
}
```
