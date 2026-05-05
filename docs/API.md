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
    "realm": "炼气一层",
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

## 灵根规则

```text
金木水火土单一属性：天灵根，修炼速度最快，例如水属性天灵根
任意两个五行属性：双灵根
任意三个五行属性：三灵根
任意四个五行属性：伪灵根
金木水火土五行俱全：杂灵根，修炼速度最慢
雷、冰、光、暗：异灵根，修炼速度约等同三灵根
```

修炼倍率由后端计算，前端只展示结果，不能伪造修炼速度。

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
    "realm": "炼气一层",
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
    "realm": "炼气一层",
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
    "realm": "炼气一层",
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

境界序列：

```text
炼气一层 -> ... -> 炼气十二层
筑基初期 -> 筑基中期 -> 筑基后期
结丹初期 -> 结丹中期 -> 结丹后期
元婴初期 -> 元婴中期 -> 元婴后期
化神初期 -> 化神中期 -> 化神后期
```

结丹后期突破到元婴初期是明显门槛；进入元婴后，每个小境界的修为需求和突破失败率都会显著增加。

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
  "message": "突破消耗 30 点行动力。突破成功！你踏入「炼气二层」。",
  "character": {
    "realm": "炼气二层",
    "cultivation": 0,
    "cultivation_cap": 120,
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
  "message": "突破消耗 30 点行动力。突破失败，心魔反噬。当前突破成功率约 61%。",
  "character": {
    "realm": "炼气一层",
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
