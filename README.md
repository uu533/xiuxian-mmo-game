# 多人在线修仙文字游戏 MVP

这是一个可运行、可测试、可验收的网络版多人在线修仙文字游戏 MVP。后端使用 Python + FastAPI + SQLAlchemy，数据库使用 SQLite，文件名固定为 `game.db`。前端使用原生 HTML + JavaScript，通过 `fetch` 调用后端 API。

## 项目目录结构

```text
.
├── backend/
│   ├── database.py          # SQLAlchemy 连接、Session、建表
│   ├── main.py              # FastAPI 应用
│   ├── models.py            # users / characters / logs 等 ORM 模型
│   ├── schemas.py           # Pydantic 请求和响应模型
│   ├── routes/
│   │   ├── auth.py          # 注册、登录
│   │   └── game.py          # 角色、行动、日志
│   └── services/
│       ├── auth_service.py  # 密码哈希、token、当前用户
│       ├── game_service.py  # 修炼、探索、战斗、突破
│       └── realm_service.py # 境界序列和突破难度
├── docs/
│   └── API.md               # 完整 API 示例
├── frontend/
│   └── index.html           # 原生 HTML + JS 前端
├── tests/
│   └── smoke_test.py        # 基础接口验收脚本
├── main.py                  # 让 uvicorn main:app --reload 可在根目录启动
├── requirements.txt
└── game.db                  # 运行后自动生成
```

## 启动步骤

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 启动后端：

```bash
uvicorn main:app --reload
```

3. 打开前端：

```text
frontend/index.html
```

也可以打开根目录的 `index.html`，它会跳转到前端页面。

## 让朋友一起测试

默认只适合本机测试。如果朋友和你在同一个 Wi-Fi 或局域网，可以把服务绑定到所有网卡：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
python -m http.server 5173 --bind 0.0.0.0
```

然后在你的电脑上查看局域网 IP，例如 Windows 执行：

```bash
ipconfig
```

找到类似 `192.168.x.x` 的 IPv4 地址。朋友访问：

```text
http://你的局域网IP:5173/frontend/index.html
```

如果朋友不在同一个网络，需要把项目部署到公网服务器，或临时使用 Cloudflare Tunnel、ngrok 这类内网穿透工具。生产环境建议改用 HTTPS，并把 SQLite 换成 PostgreSQL/MySQL 之类的服务端数据库。

## 已实现玩法

- 用户注册、登录、token 身份验证。
- 每个账号独立角色数据，存入 `game.db`。
- 角色字段：境界、修为、修为上限、灵根、年龄、寿元、气血、法力、功法加成、法宝加成、心魔、气运、灵石。
- 境界：炼气一至十二层；筑基、结丹、元婴、化神均分初期、中期、后期。
- 难度：结丹后期冲击元婴成功率显著降低；元婴之后每个小境界的修为需求和突破难度都会大幅提升。
- 灵根：金木水火土单一属性为天灵根，双属性为双灵根，三属性为三灵根，四属性为伪灵根，五属性为杂灵根；雷、冰、光、暗为异灵根。
- 修炼速度：天灵根最快，杂灵根最慢，异灵根速度约等同三灵根。角色页灵根旁的 `?` 可查看简明说明。
- 称号：角色名后可挂称号；炼气期默认解锁师兄/师姐，结丹期解锁道人、真人、老祖、真君、尊者，元婴与化神继续解锁更高称号。
- 身份：主页面年龄后显示身份状态；无宗门为散修，有宗门时显示 `宗门名 · 宗门地位`。
- 宗门地位：炼气期对应外门弟子、内门弟子、亲传弟子；筑基期对应外门执事、内门执事、副掌门；结丹期对应分支长老、普通长老、高阶长老、核心长老、名义长老、供奉长老；元婴期对应太上长老、大长老、宗门领袖。
- 气血：气血是生命值，前端会标注 `0 则死亡` 并显示当前生命状态。
- 气运、心魔：后端保留，用于影响成功率、收益和未来玩法；前端默认不显示，玩家不能直接查看自己的气运和心魔数值。
- 寿元：按境界自动计算。炼气一至五层 100 岁，炼气六至十二层 130 岁，筑基期 200 岁，结丹期 500 岁，元婴期 1000 岁，化神期 3000 岁。
- 攻击/防御：由境界基础值 + 功法加成 + 法宝加成计算，前端展示最终值和来源拆分，不再依赖固定数据库字段。
- 行动：打坐修炼、外出探索、突破境界、查看角色、查看日志。
- 法力：所有主要行为消耗法力。打坐修炼消耗 12 点，外出探索消耗 18 点，突破境界消耗 35 点。法力不足时操作失败，并提示可通过调息、吸收灵石或服用丹药恢复。
- 法力恢复：新增打坐恢复法力、吸收灵石恢复法力、服用丹药恢复法力。
- 年龄：不再由行动指令直接增加，寿元表示年龄上限。
- 背包：前端与 API 返回固定 9x9 共 81 个格子；探索物品会占用格子，储物袋与灵兽袋作为后续扩展。
- 探索随机结果：获得灵石、获得物品、触发简单回合制战斗。
- 突破有成功率，成功进入下个境界，失败会损失状态并增加心魔。
- 每次操作都会写入独立玩家日志。

## 数据库设计

核心表：

- `users`：`id`, `username`, `password_hash`, `created_at`
- `characters`：`user_id`, `title`, `sect_name`, `sect_branch`, `realm`, `cultivation`, `cultivation_cap`, `spiritual_root`, `age`, `lifespan`, `hp`, `mana`, `cultivation_method_attack_bonus`, `cultivation_method_defense_bonus`, `cultivation_method_mana_bonus`, `magic_treasure_attack_bonus`, `magic_treasure_defense_bonus`, `magic_treasure_mana_bonus`, `inner_demon`, `luck`, `spirit_stones`
- `logs`：`user_id`, `content`, `created_at`

扩展表：

- `auth_tokens`：保存登录 token。
- `inventory_items`：保存探索获得的物品。

## 测试方法

启动后端后运行：

```bash
python tests/smoke_test.py
```

该脚本会验证注册多个账号、token 登录、数据隔离、法力消耗与恢复、固定格子背包、隐藏气运心魔、寿元规则、修炼、探索、突破、日志写入和数据持久化读取。

完整 API 请求和返回示例见 [docs/API.md](docs/API.md)。
