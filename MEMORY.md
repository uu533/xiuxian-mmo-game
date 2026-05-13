# MEMORY.md - 修仙 MMO 项目长期记忆

> 创建时间：2026-05-13
> 更新：2026-05-13（main 合并完成，更新稳定点）

---

## 一、项目定位

**项目名称：** 修仙 MMO 游戏（xiuxian-mmo-game）
**类型：** 放置养成类回合制 MMO
**技术栈：** Python 后端（Flask） + 单文件 HTML 前端
**当前 main 最新稳定点：** `f3e4cea`（Merge life skills UI recipes branch）
**已推送稳定 tag：** `stable-life-skills-ui-recipes-v1.2`

---

## 二、AI 分工

| 角色 | 职责 |
|------|------|
| **ChatGPT** | 设计评审、任务拆解、风险判断、合并建议 |
| **Codex** | 主线守门员、Git 安全检查、最终测试、合并执行 |
| **OpenClaw** | 实验分支开发 Agent，只做小步开发和修复 |

---

## 三、核心设计原则

1. **所有核心逻辑必须在后端**
2. **所有数值必须在 configs + calc_service**
3. **所有行为必须走 /action/execute**
4. **所有内容必须可配置**
5. **不允许出现单一最优玩法**
6. **探索必须是核心资源来源**
7. **法力是唯一行动资源**
8. **气运、心魔等隐藏属性不能直接前端展示**
9. **生活技能是资源转化器，不是资源生产器**
10. **宗门系统提供长期目标，但不能替代探索**

---

## 四、已完成系统

- [x] 法力驱动
- [x] 探索 / 掉落 / 机缘
- [x] 功法成长
- [x] 法宝强化
- [x] 瓶颈突破
- [x] 81 格背包
- [x] /action/execute
- [x] simulation
- [x] 新手任务
- [x] 宗门系统
- [x] 生活技能系统
- [x] active_effects
- [x] /life-skills/recipes

---

## 五、生活技能系统状态

### 四类生活技能

| 技能 | action_type | 配方来源 |
|------|-------------|----------|
| 炼丹 | alchemy | configs/recipes_alchemy.py |
| 制符 | talisman | configs/recipes_talisman.py |
| 炼器 | crafting | configs/recipes_crafting.py |
| 阵法 | formation | configs/recipes_formation.py |

### 配方接口
- **接口路径：** `GET /life-skills/recipes`
- **数据来源：** `backend/configs/recipes_*.py`（无重复硬编码）
- **前端读取：** `loadRecipes()` 异步请求，存入 `fetchedRecipes` 变量

### 制作流程
- 制作仍走 `/action/execute`，action_type 为 `alchemy` / `talisman` / `crafting` / `formation`
- 前端不计算核心收益，后端处理

---

## 六、正确 action_type 映射

| 物品类型 | 按钮文字 | action_type |
|----------|----------|-------------|
| cultivation_method | 学习 | learn_method |
| magic_artifact | 装备 | equip_artifact |
| pill | 服用 | use_item |
| talisman | 使用 | use_item |
| alchemy | 制作炼丹 | alchemy |
| talisman（制作） | 制作符箓 | talisman |
| crafting | 制作炼器 | crafting |
| formation | 激活阵法 | formation |

> ⚠️ 注意：action_type 小写，route 名用小写。

---

## 七、active_effects 规则

- **数值显示：** value < 1 且 > 0 → 显示百分比；value >= 1 → 原样显示数字
- **触发：** 使用丹药/符箓后 active_effects 增加
- **扣减：** 每次行动扣减，有持续时间
- **消失：** 倒计时归零后移除

---

## 八、已知重要问题

1. **"配方加载失败：Not Found"**
   - 根因：8000 端口运行的是旧后端（未包含 `/life-skills/recipes` 接口）
   - 解决：必须用当前代码重新启动 8000 后端
   - 验收前必须确认浏览器连接的是当前代码启动的后端

2. **action 映射回归（已修复并合并）**
   - 功法 learn_method、法宝 equip_artifact 不能发给 use_item
   - 修复代码在 frontend/index.html

---

## 九、Git 规则

### 允许的 Git 操作
```bash
git branch --show-current
git status
git log --oneline -n 5
git diff
git diff --stat
git add
git commit
git push origin <实验分支>
```

### 严禁操作
- ❌ git push origin main
- ❌ git push --force / -f
- ❌ git reset --hard
- ❌ git clean
- ❌ git merge main / origin/main（除非人工 review 通过）
- ❌ git rebase
- ❌ git branch -D / -d
- ❌ git push origin --delete

### main 分支
- **不允许直接修改**
- 所有改动通过 PR / 人工 review 合并
- **当前稳定点：** `f3e4cea`（Merge life skills UI recipes branch）
- **稳定 tag：** `stable-life-skills-ui-recipes-v1.2`

---

## 十、严禁改动的文件

除非用户明确要求，否则禁止改动：

- backend/database.py
- backend/models/
- backend/schemas/
- main.py
- backend/main.py
- README.md
- docs/API.md

---

## 十一、当前分支状态

| 分支 | 状态 | OpenClaw 能否操作 |
|------|------|-------------------|
| `main` | 稳定，f3e4cea | ❌ 禁止直接修改 |
| `ai/lab-life-skills-content` | 已合并完成，不再使用 | ❌ 禁止继续开发 |
| `ui/pc-responsive-layout` | Codex 维护，PC UI 响应式 | ❌ 禁止 OpenClaw 参与 |
| `ai/lab-life-skills-content-v2` | **待创建**，基于最新 main | ✅ 下一轮实验分支 |

### 运行进程状态
- **8000：** 当前 merged main 后端，PID 9492
- **8005：** 隔离后端，PID 58836
- **5174：** 前端静态服务，PID 72804

---

## 十二、合并后测试结果（f3e4cea）

- ✅ python -m compileall backend 通过
- ✅ smoke_test 通过
- ✅ simulation 3h / 12h / 24h with_sect=true 均健康
- ✅ 未发现只修炼最优
- ✅ 未发现只炼丹最优
- ✅ 未发现只阵法最优
- ✅ 未发现探索异常下降
- ✅ 未发现生活技能收益失控
- ✅ 未发现法力循环失控
- ✅ 未发现宗门推进异常
- ✅ 未发现 P0/P1

---

## 十三、下一阶段方向

| 角色 | 方向 |
|------|------|
| **Codex** | PC 浏览器 UI 响应式适配（ui/pc-responsive-layout 分支） |
| **OpenClaw** | 生活技能内容扩展 v2（从 `ai/lab-life-skills-content-v2` 新分支，基于最新 main） |
| **ChatGPT** | 目标链系统、死亡轮回、玩法灵魂设计 |

---

## 十四、OpenClaw 下一轮任务

**等待用户确认后，从最新 main 创建新实验分支 `ai/lab-life-skills-content-v2`，继续生活技能内容扩展 v2。**

### 禁止事项
- ❌ 继续在 `ai/lab-life-skills-content` 开发（已合并，废弃）
- ❌ 碰 `ui/pc-responsive-layout` 分支
- ❌ 开发 PC UI 相关功能
- ❌ merge main
- ❌ push main
- ❌ force push / reset --hard / git clean

---

## 十五、会话启动规则

每次新会话必须先读：
1. `MEMORY.md`（本文件）
2. `memory/YYYY-MM-DD.md`（当天记录）
3. `generator-log.md`（最新开发日志）
4. `BRANCH_POLICY.md`
5. `AI_WORKSPACE_RULES.md`

检查分支、commit、状态后，输出"上下文恢复报告"，等待用户明确任务后再开发。

---

## 十六、禁止操作

- ❌ 直接开始开发（未恢复上下文前）
- ❌ merge main（除非人工 review 通过）
- ❌ push main
- ❌ force push
- ❌ reset --hard
- ❌ git clean
- ❌ 删除核心文件
- ❌ 切到 dev/next-major
- ❌ 在 `ai/lab-life-skills-content` 继续开发
- ❌ 参与 `ui/pc-responsive-layout` 相关工作
- ❌ 大规模重构
- ❌ 修改数据库结构

---

## 十七、OpenClaw 固定技能

OpenClaw 每次任务前后必须读取并遵守 `skills/` 下的固定技能文档：

| 文档 | 用途 |
|------|------|
| `skills/QUEST_ANTI_DEADLOCK.md` | 任务防卡死检查 |
| `skills/LOCALIZATION_ZH_CHECK.md` | 中文化检查 |
| `skills/PLAYER_FLOW_QA.md` | 玩家路径验收 |
| `skills/TEST_DISCIPLINE.md` | 测试纪律 |
| `skills/GIT_SAFETY.md` | Git 安全 |
| `skills/COMPLETION_REPORT_TEMPLATE.md` | 完成报告模板 |

### 硬规则

- 测试没跑完，不允许说完成
- 玩家路径没走通，不允许说完成
- 任务可能卡死，不允许提交
- 玩家可见英文必须修复或报告
- 不允许把临时文件混入提交
- 不允许直接操作 main
- 每次新会话必须先读 skills/ 再开始开发
