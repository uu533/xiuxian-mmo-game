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

查看角色信息和 81 格固定背包。气运和心魔由后端保留，但默认不返回给前端。

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
    "title": "师兄",
    "unlocked_titles": ["师兄", "师姐"],
    "life_status": "存活",
    "sect_name": null,
    "sect_branch": null,
    "sect_position": "散修",
    "identity_status": "散修",
    "realm": "炼气一层",
    "cultivation": 0,
    "cultivation_cap": 80,
    "spiritual_root": "水属性天灵根",
    "age": 16,
    "lifespan": 100,
    "hp": 108,
    "mana": 100,
    "max_mana": 100,
    "attack": 5,
    "defense": 5,
    "spirit_stones": 100,
    "attack_base": 5,
    "defense_base": 5,
    "attack_bonus": 0,
    "defense_bonus": 0,
    "mana_bonus": 0
  },
  "inventory": [
    {
      "slot_index": 1,
      "name": null,
      "quantity": 0
    }
  ]
}
```

`inventory` 实际固定返回 81 个格子，上例只截取第 1 格。

## POST /character/title

修改角色称号。称号必须已经被当前境界解锁。

请求示例：

```json
{
  "title": "师姐"
}
```

返回示例：

```json
{
  "message": "你将称号改为「师姐」。",
  "character": {
    "title": "师姐",
    "realm": "炼气一层"
  },
  "inventory": []
}
```

称号解锁：

```text
炼气期：师兄、师姐
筑基期：师叔、师伯、前辈
结丹期：道人、真人、老祖、真君、尊者
元婴期：大修士、元君、天君、法王、上人
化神期：道尊、神君、圣君、尊上
```

## 身份状态与宗门地位

角色未加入宗门时：

```json
{
  "identity_status": "散修",
  "sect_position": "散修"
}
```

有宗门时，主界面年龄后显示：

```text
宗门名 · 宗门地位
```

宗门地位规则：

```text
炼气一至四层：外门弟子
炼气五至九层：内门弟子
炼气十至十二层：亲传弟子
筑基初期：外门执事
筑基中期：内门执事
筑基后期：副掌门
结丹初期：XX峰/XX宫长老
结丹中期：普通长老、高阶长老
结丹后期：核心长老、名义长老、供奉长老
元婴初期：太上长老
元婴中期：大长老
元婴后期：宗门领袖
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

## 境界、寿元、战斗属性

境界序列：

```text
炼气一层 -> ... -> 炼气十二层
筑基初期 -> 筑基中期 -> 筑基后期
结丹初期 -> 结丹中期 -> 结丹后期
元婴初期 -> 元婴中期 -> 元婴后期
化神初期 -> 化神中期 -> 化神后期
```

寿元规则：

```text
炼气一至五层：100 岁
炼气六至十二层：130 岁
筑基期：200 岁
结丹期：500 岁
元婴期：1000 岁
化神期：3000 岁
```

攻击/防御由后端计算：

```text
最终攻击 = 境界基础攻击 + 功法攻击加成 + 法宝攻击加成
最终防御 = 境界基础防御 + 功法防御加成 + 法宝防御加成
```

## POST /action/train

打坐修炼，消耗 12 点法力，增加修为，可能轻微增加心魔。年龄不随单次行动增长。

请求示例：

```http
POST /action/train
Authorization: Bearer <token>
```

返回示例：

```json
{
  "message": "打坐修炼消耗 12 点法力，炼化灵气，修为增加 24。",
  "character": {
    "realm": "炼气一层",
    "cultivation": 24,
    "cultivation_cap": 80,
    "mana": 88,
    "max_mana": 100
  },
  "inventory": []
}
```

法力不足返回示例：

```json
{
  "message": "法力不足，本次需要 12 点，当前只有 0 点。法力不足，可通过打坐恢复法力、吸收灵石恢复法力，或服用丹药恢复法力。"
}
```

## POST /action/explore

外出探索，消耗 18 点法力，随机获得灵石、物品或触发简单回合制战斗。

请求示例：

```http
POST /action/explore
Authorization: Bearer <token>
```

返回示例：

```json
{
  "message": "外出探索消耗 18 点法力，采得 聚气散 x2。",
  "character": {
    "realm": "炼气一层",
    "cultivation": 38,
    "mana": 70,
    "spirit_stones": 100
  },
  "inventory": [
    {
      "slot_index": 1,
      "name": "聚气散",
      "quantity": 2
    }
  ]
}
```

## POST /action/breakthrough

突破境界。修为必须达到上限，消耗 35 点法力。结丹后期突破到元婴初期是明显门槛；进入元婴后，每个小境界的修为需求和突破失败率都会显著增加。

请求示例：

```http
POST /action/breakthrough
Authorization: Bearer <token>
```

成功返回示例：

```json
{
  "message": "突破消耗 35 点法力。突破成功！你踏入「炼气二层」。",
  "character": {
    "realm": "炼气二层",
    "cultivation": 0,
    "cultivation_cap": 120,
    "lifespan": 100,
    "mana": 120,
    "max_mana": 120
  },
  "inventory": []
}
```

失败返回示例：

```json
{
  "message": "突破消耗 35 点法力。突破失败，心魔反噬。当前突破成功率约 61%。"
}
```

## POST /action/meditate

打坐恢复法力，不消耗灵石或物品。

请求示例：

```http
POST /action/meditate
Authorization: Bearer <token>
```

返回示例：

```json
{
  "message": "静坐调息，恢复 30 点法力。"
}
```

## POST /action/spirit-stone

吸收灵石恢复法力。当前规则为消耗 10 枚灵石，恢复 60 点法力。

请求示例：

```http
POST /action/spirit-stone
Authorization: Bearer <token>
```

返回示例：

```json
{
  "message": "手握灵石吸取灵力，消耗 10 灵石，恢复 60 点法力。"
}
```

## POST /action/pill

服用回灵丹恢复法力。回灵丹可通过探索获得。

请求示例：

```http
POST /action/pill
Authorization: Bearer <token>
```

返回示例：

```json
{
  "message": "服下一枚回灵丹，恢复 100 点法力。"
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
    "content": "打坐修炼消耗 12 点法力，炼化灵气，修为增加 24。",
    "created_at": "2026-05-05T03:20:00.123456"
  }
]
```
