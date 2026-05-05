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
- 角色字段：境界、修为、修为上限、灵根、年龄、寿元、气血、法力、攻击、防御、心魔、气运、灵石、行动力。
- 境界：炼气一至十二层；筑基、结丹、元婴、化神均分初期、中期、后期。
- 难度：结丹后期冲击元婴成功率显著降低；元婴之后每个小境界的修为需求和突破难度都会大幅提升。
- 行动：打坐修炼、外出探索、突破境界、查看角色、查看日志。
- 行动力：上限 100，每 10 分钟自然恢复 5 点。打坐消耗 10 点，探索消耗 15 点，突破消耗 30 点。
- 年龄：不再随每次指令直接增加，累计消耗 1000 点行动力才增长 1 岁。寿元表示寿元上限，突破境界会提升寿元上限。
- 探索随机结果：获得灵石、获得物品、触发简单回合制战斗。
- 突破有成功率，成功进入下个境界，失败会损失状态并增加心魔。
- 每次操作都会写入独立玩家日志。

## 数据库设计

核心表：

- `users`：`id`, `username`, `password_hash`, `created_at`
- `characters`：`user_id`, `realm`, `cultivation`, `cultivation_cap`, `spiritual_root`, `age`, `lifespan`, `hp`, `mana`, `attack`, `defense`, `inner_demon`, `luck`, `spirit_stones`, `action_points`, `max_action_points`, `action_spent_total`, `age_progress`, `last_action_recovered_at`
- `logs`：`user_id`, `content`, `created_at`

扩展表：

- `auth_tokens`：保存登录 token。
- `inventory_items`：保存探索获得的物品。

## 测试方法

启动后端后运行：

```bash
python tests/smoke_test.py
```

该脚本会验证注册多个账号、token 登录、数据隔离、修炼、探索、突破、日志写入和数据持久化读取。

完整 API 请求和返回示例见 [docs/API.md](docs/API.md)。
