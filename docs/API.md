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
  "inventory": []
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
