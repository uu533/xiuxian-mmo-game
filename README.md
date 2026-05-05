# 多人在线修仙文字游戏

这是一个 FastAPI + SQLAlchemy + SQLite 的网络版修仙文字游戏 MVP。当前版本已经从单文件 MVP 重构为分层后端：模型、接口模型、路由、业务服务、仓储、配置和工具函数分离，方便后续扩展宗门、社交、交易、PVP、功法、法宝、丹药、灵兽、洞府、秘境和副本。

## 新项目结构

```text
backend/
  main.py
  database.py
  configs/
    actions.py
    events.py
    formulas.py
    items.py
    realms.py
  models/
    character.py
    inventory.py
    item.py
    log.py
    progression.py
    sect.py
    social.py
    user.py
  repositories/
    character_repo.py
    inventory_repo.py
    log_repo.py
    user_repo.py
  routes/
    action.py
    auth.py
    character.py
    dev.py
    inventory.py
    log.py
  schemas/
    action.py
    auth.py
    character.py
    inventory.py
    log.py
  services/
    action_service.py
    auth_service.py
    calc_service.py
    character_service.py
    event_service.py
    inventory_service.py
    log_service.py
    realm_service.py
    sect_service.py
    spiritual_root_service.py
  utils/
    random_utils.py
    security.py
    time_utils.py
frontend/
  index.html
tests/
  smoke_test.py
```

## 启动

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

前端可以直接打开：

```text
frontend/index.html
```

多人局域网测试：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
python -m http.server 5173 --bind 0.0.0.0
```

## 数据库结构

核心表：

- `users`：账号、密码哈希、创建时间、最近登录时间、状态。
- `characters`：角色主数据，包含姓名、称号、境界、修为、灵根、年龄、寿元、气血、法力、基础攻防、隐藏气运、隐藏心魔、灵石、宗门引用。
- `character_derived_stats`：预留最终属性快照表。当前接口由 `calc_service.py` 动态计算最终属性，避免早期频繁调数导致快照过期；该表保留给后续排行榜、战力缓存和离线结算。
- `item_templates`：物品模板，集中配置丹药、材料、法宝、功法、储物袋、灵兽袋、任务物品。
- `inventory_slots`：固定格子背包。主背包固定 81 格，储物袋、灵兽袋也共用同一套 slot 结构。
- `item_instances`：不可堆叠物品实例，预留法宝、功法、储物袋等成长属性。
- `character_methods`：角色已学功法。
- `character_artifacts`：角色装备法宝。
- `game_logs`：结构化日志，`content` 给玩家看，`data_json` 给系统分析和前端扩展。
- `action_records`：统一行为记录，保存行为消耗和结果。
- `sects`、`sect_members`：宗门系统预留。
- `friendships`、`messages`：好友、私聊、世界聊天预留。

旧版 `logs` 和 `inventory_items` 表如果已经存在会保留在数据库中，但新逻辑不再依赖它们。

## 迁移与重建

方案 A：保留旧库自动迁移

启动服务时会自动执行：

- 创建新表。
- 为 `users`、`characters` 补充新字段。
- 将旧 `luck / inner_demon` 迁移到 `hidden_luck / hidden_inner_demon`。
- 尝试删除旧行动力字段。
- 为已有角色补齐 81 个主背包格子。
- 写入基础物品模板。

方案 B：删除数据库重建

早期开发阶段推荐在结构大改后使用：

```text
停止服务
删除项目根目录的 game.db
重新执行 uvicorn main:app --reload
重新注册测试账号
```

如果旧库过于混乱导致迁移失败，后端错误信息会提示删除 `game.db` 后重建。

## 主要规则

- 所有核心逻辑在后端，前端只展示和请求。
- 行为统一走 `POST /action/execute`。
- 修炼、探索、突破消耗法力，不再使用行动力。
- 法力不足时行为失败，并提示恢复方式。
- 恢复法力行为：打坐调息、吸收灵石、使用回灵丹。
- 气运、心魔后端保留，普通角色接口不返回具体数值。
- 寿元按境界自动计算：炼气 1-5 层 100 岁，炼气 6-12 层 130 岁，筑基 200 岁，结丹 500 岁，元婴 1000 岁，化神 3000 岁。
- 攻击/防御统一由 `calc_service.py` 计算：基础值 + 功法效果 + 法宝效果 + 状态效果。
- 探索事件由 `configs/events.py` 配置，气运影响稀有事件、收益和负面事件权重。

## 测试

启动后端后运行：

```bash
python tests/smoke_test.py
```

覆盖：注册两个账号、数据隔离、角色查询、无行动力字段、法力消耗与恢复、探索事件、结构化日志、突破日志、固定 81 格背包、物品入包、隐藏气运心魔、dev health、重新登录后数据持久。

## API

详见 [docs/API.md](docs/API.md)。
