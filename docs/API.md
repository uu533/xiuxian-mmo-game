# API 设计

默认后端地址：

```text
http://127.0.0.1:8000
```

除注册和登录外，其他接口都需要请求头：

```http
Authorization: Bearer <token>
```

## POST /register

注册账号，并返回 token。

请求示例：

```json
{
  "username": "player01",
  "password": "123456"
}
```

返回示例：

```json
{
  "token": "VgLeLqK...",
  "username": "player01"
}
```

## POST /login

登录账号，并返回 token。

请求示例：

```json
{
  "username": "player01",
  "password": "123456"
}
```

返回示例：

```json
{
  "token": "FAnS9rv...",
  "username": "player01"
}
```

## GET /me

查看角色信息和背包。

请求示例：

```http
GET /me
Authorization: Bearer <token>
```

返回示例：

```json
{
  "username": "player01",
  "character": {
    "realm": "炼气",
    "cultivation": 0,
    "cultivation_cap": 100,
    "spiritual_root": "三灵根",
    "age": 16,
    "lifespan": 80,
    "hp": 108,
    "mana": 64,
    "attack": 14,
    "defense": 7,
    "inner_demon": 0,
    "luck": 61,
    "spirit_stones": 100,
    "action_points": 100,
    "max_action_points": 100,
    "action_spent_total": 0,
    "age_progress": 0
  },
  "inventory": []
}
```

## POST /action/train

打坐修炼，消耗 10 点行动力，增加修为，可能增加心魔。年龄不随单次行动直接增长。

请求示例：

```http
POST /action/train
Authorization: Bearer <token>
```

返回示例：

```json
{
  "message": "打坐修炼消耗 10 点行动力，吸纳灵气，修为增加 24。",
  "character": {
    "realm": "炼气",
    "cultivation": 24,
    "cultivation_cap": 100,
    "spiritual_root": "三灵根",
    "age": 16,
    "lifespan": 80,
    "hp": 108,
    "mana": 66,
    "attack": 14,
    "defense": 7,
    "inner_demon": 0,
    "luck": 61,
    "spirit_stones": 100,
    "action_points": 90,
    "max_action_points": 100,
    "action_spent_total": 10,
    "age_progress": 10
  },
  "inventory": []
}
```

## POST /action/explore

外出探索，消耗 15 点行动力，随机获得灵石、物品或触发战斗。

请求示例：

```http
POST /action/explore
Authorization: Bearer <token>
```

返回示例：

```json
{
  "message": "外出探索采得 聚气散 x2。",
  "character": {
    "realm": "炼气",
    "cultivation": 38,
    "cultivation_cap": 100,
    "spiritual_root": "三灵根",
    "age": 18,
    "lifespan": 80,
    "hp": 108,
    "mana": 66,
    "attack": 14,
    "defense": 7,
    "inner_demon": 0,
    "luck": 61,
    "spirit_stones": 100
  },
  "inventory": [
    {
      "name": "聚气散",
      "quantity": 2
    }
  ]
}
```

战斗返回示例：

```json
{
  "message": "遭遇黑鳞妖蛇，战斗开始。 第1回合，你造成 17 伤害。 黑鳞妖蛇反击，你损失 8 气血。 黑鳞妖蛇败退。 战后搜得 52 灵石。",
  "character": {
    "realm": "炼气",
    "cultivation": 44,
    "cultivation_cap": 100,
    "spiritual_root": "三灵根",
    "age": 19,
    "lifespan": 80,
    "hp": 100,
    "mana": 66,
    "attack": 14,
    "defense": 7,
    "inner_demon": 0,
    "luck": 61,
    "spirit_stones": 152
  },
  "inventory": []
}
```

## POST /action/breakthrough

突破境界。修为必须达到上限，消耗 30 点行动力。突破存在成功率，可能成功或失败。

## 行动力与年龄规则

```text
行动力上限：100
自然恢复：每 10 分钟恢复 5 点
打坐修炼：消耗 10 点
外出探索：消耗 15 点
突破境界：消耗 30 点
年龄增长：累计消耗 1000 点行动力，年龄增加 1 岁
```

寿元表示角色寿元上限，不再被每次行动直接扣减。突破成功会提高寿元上限。

请求示例：

```http
POST /action/breakthrough
Authorization: Bearer <token>
```

成功返回示例：

```json
{
  "message": "突破成功！你踏入「筑基」，寿元与法力大涨。",
  "character": {
    "realm": "筑基",
    "cultivation": 0,
    "cultivation_cap": 260,
    "spiritual_root": "三灵根",
    "age": 23,
    "lifespan": 125,
    "hp": 144,
    "mana": 94,
    "attack": 22,
    "defense": 12,
    "inner_demon": 0,
    "luck": 61,
    "spirit_stones": 152
  },
  "inventory": []
}
```

失败返回示例：

```json
{
  "message": "突破失败，心魔反噬。当前突破成功率约 61%。",
  "character": {
    "realm": "炼气",
    "cultivation": 42,
    "cultivation_cap": 100,
    "spiritual_root": "三灵根",
    "age": 23,
    "lifespan": 80,
    "hp": 91,
    "mana": 66,
    "attack": 14,
    "defense": 7,
    "inner_demon": 15,
    "luck": 61,
    "spirit_stones": 152
  },
  "inventory": []
}
```

## GET /logs

查看玩家独立日志。

请求示例：

```http
GET /logs?limit=30
Authorization: Bearer <token>
```

返回示例：

```json
[
  {
    "id": 3,
    "content": "打坐一载，吸纳灵气，修为增加 24。",
    "created_at": "2026-05-05T03:20:00.123456"
  },
  {
    "id": 2,
    "content": "你回到洞府，重新接续修行。",
    "created_at": "2026-05-05T03:19:00.123456"
  }
]
```
