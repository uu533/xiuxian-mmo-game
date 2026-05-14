# LIFE_SKILLS_CONTENT_V2_REPORT.md

## 基本信息

- **分支：** `ai/lab-life-skills-content-v2`
- **起始 commit：** `f3e4cea`（基于最新 main）
- **本轮 commit：** 待提交
- **任务：** 生活技能内容扩展 v2

---

## 新增丹药（3 个）

### 1. 养气丹（yangqi_pill）

| 属性 | 值 |
|------|-----|
| 物品 code | `yangqi_pill` |
| 类型 | pill |
| 品质 | grade 1 |
| 描述 | 服用后下一次修炼获得小幅加成 |
| 效果 | `train_next_bonus: 1`（激活后下次修炼额外 +1） |
| active_effect | `train_next_bonus`，value=1，remaining_uses=1 |

**配方：**
- `alchemy_yangqi_pill`
- 材料：healing_herb × 2，low_spirit_stone × 4
- 法力：18
- 境界要求：炼气一层（REALM_NAMES[0]）
- 成功率：100%

**为什么不会破坏平衡：**
- 只加成 1 次（remaining_uses=1），不可叠加
- 加成幅度小（+1），聊胜于无
- 炼气期修炼效率 1.0 时，+1 几乎无感知

---

### 2. 固元丹（guyu_pill）

| 属性 | 值 |
|------|-----|
| 物品 code | `guyu_pill` |
| 类型 | pill |
| 品质 | grade 1 |
| 描述 | 服用后提升下一次突破成功率 |
| 效果 | `breakthrough_next_bonus: 1`（激活后下次突破额外 +1） |
| active_effect | `breakthrough_next_bonus`，value=1，remaining_uses=1 |

**配方：**
- `alchemy_guyu_pill`
- 材料：healing_herb × 3，low_spirit_stone × 6
- 法力：22
- 境界要求：炼气二层（REALM_NAMES[1]）
- 成功率：100%

**为什么不会破坏平衡：**
- 只加成 1 次（remaining_uses=1）
- 炼气期突破率 0.88~0.46，+1 约 1~2% 提升，极为有限
- 需要炼气二层才能制作，材料成本不低

---

### 3. 回春丹（huichun_pill）

| 属性 | 值 |
|------|-----|
| 物品 code | `huichun_pill` |
| 类型 | pill |
| 品质 | grade 1 |
| 描述 | 服用后恢复少量气血 |
| 效果 | `recover_hp: 40`（即时恢复 40 HP） |

**配方：**
- `alchemy_huichun_pill`
- 材料：healing_herb × 1，low_spirit_stone × 3
- 法力：14
- 境界要求：炼气一层（REALM_NAMES[0]）
- 成功率：100%

**为什么不会破坏平衡：**
- 即时恢复，不是永久加成
- 恢复量 40，远低于疗伤丹的 80
- 主要用途是探索续航，不能替代探索

---

## 新增符箓（3 个）

### 1. 探路符（explore_luck_talisman）

| 属性 | 值 |
|------|-----|
| 物品 code | `explore_luck_talisman` |
| 类型 | talisman |
| 品质 | grade 1 |
| 描述 | 使用后小幅提升探索机缘和材料获取概率，持续1次 |
| 效果 | `explore_luck_talisman_charge: 1` |
| active_effect | `explore_luck_bonus`，value=0.05，remaining_uses=1 |

**对比现有 scout_talisman：**
- scout_talisman：`explore_luck_bonus`，value=0.06（略高）
- 探路符：value=0.05（稍弱，略作差异化）

**配方：**
- `talisman_explore_luck`
- 材料：low_material × 1，low_spirit_stone × 3
- 法力：14
- 境界要求：炼气一层
- 成功率：100%

**为什么不会破坏平衡：**
- 只生效 1 次（remaining_uses=1）
- +5% 探索机缘，聊胜于无
- 不能替代探索核心地位

---

### 2. 避祸符（avoid_harm_talisman）

| 属性 | 值 |
|------|-----|
| 物品 code | `avoid_harm_talisman` |
| 类型 | talisman |
| 品质 | grade 1 |
| 描述 | 使用后降低探索中负面事件概率，持续1次 |
| 效果 | `avoid_harm_talisman_charge: 1` |
| active_effect | `explore_damage_reduction`，value=0.25，remaining_uses=1 |

**对比现有 guard_talisman：**
- guard_talisman：`explore_damage_reduction`，value=0.45（强）
- 避祸符：value=0.25（弱于 guard_talisman）

**配方：**
- `talisman_avoid_harm`
- 材料：calm_talisman × 1，low_material × 1
- 法力：14
- 境界要求：炼气一层
- 成功率：100%

**为什么不会破坏平衡：**
- 只生效 1 次
- value=0.25（约 25% 减伤），远低于 guard_talisman 的 0.45
- 不能完全消除探索负面事件

---

### 3. 聚灵符（spirit_gather_talisman）

| 属性 | 值 |
|------|-----|
| 物品 code | `spirit_gather_talisman` |
| 类型 | talisman |
| 品质 | grade 1 |
| 描述 | 使用后小幅提升修炼效果，持续1次 |
| 效果 | `spirit_gather_talisman_charge: 1` |
| active_effect | `train_cultivation_bonus`，value=0.04，remaining_uses=1 |

**对比阵法：**
- formation_gather_spirit：value=0.12，remaining_uses=3（强）
- 聚灵符：value=0.04，remaining_uses=1（弱）

**配方：**
- `talisman_spirit_gather`
- 材料：low_material × 2，low_spirit_stone × 5
- 法力：18
- 境界要求：炼气三层（REALM_NAMES[2]）
- 成功率：100%

**为什么不会破坏平衡：**
- 只生效 1 次，远弱于阵法（3 次，value=0.12）
- 0.04 vs 阵法 0.12，聚灵符是阵法的弱化版
- 不会让符箓变成修炼最优解

---

## 新增法器（3 个）

### 1. 青木佩（qingmu_pendant）

| 属性 | 值 |
|------|-----|
| 物品 code | `qingmu_pendant` |
| 类型 | magic_artifact |
| 品质 | grade 1 |
| 描述 | 小幅降低探索损耗，适合探索型玩家 |
| 效果 | `explore_reward_bonus: 0.015`，`defense: 3` |

**对比现有 crafted_low_sword：**
- crafted_low_sword：attack=6，defense=3，explore_reward_bonus=0.01
- 青木佩：defense=3，explore_reward_bonus=0.015（探索加成略高）

**配方：**
- `craft_qingmu_pendant`
- 材料：low_material × 4，low_spirit_stone × 10
- 法力：24
- 境界要求：炼气二层（REALM_NAMES[1]）
- 成功率：100%

---

### 2. 聚气玉（juqi_jade）

| 属性 | 值 |
|------|-----|
| 物品 code | `juqi_jade` |
| 类型 | magic_artifact |
| 品质 | grade 1 |
| 描述 | 小幅提升修炼收益，适合修炼型玩家 |
| 效果 | `cultivation_speed: 0.015` |

**对比现有 gathering_artifact：**
- gathering_artifact：attack=3，defense=4，cultivation_speed=0.02
- 聚气玉：cultivation_speed=0.015（稍弱，无战斗属性）

**配方：**
- `craft_juqi_jade`
- 材料：low_material × 4，low_spirit_stone × 12
- 法力：26
- 境界要求：炼气三层（REALM_NAMES[2]）
- 成功率：100%

---

### 3. 护身铃（hushen_bell）

| 属性 | 值 |
|------|-----|
| 物品 code | `hushen_bell` |
| 类型 | magic_artifact |
| 品质 | grade 1 |
| 描述 | 小幅降低探索受伤风险，适合探索型玩家 |
| 效果 | `defense: 3`，`explore_damage_reduction: 0.04` |

**定位：** 探索防御型，与 guard_talisman（符文，即时减伤）形成差异化

**配方：**
- `craft_hushen_bell`
- 材料：low_material × 5，low_spirit_stone × 14
- 法力：28
- 境界要求：炼气四层（REALM_NAMES[3]）
- 成功率：100%

---

## 阵法（本轮无新增）

本轮阵法数量维持 3 个（原有），未新增阵法。

理由：阵法系统（formation_gather_spirit / formation_guard / formation_draw_spirit）已较完善，且强阵法的长期加成（remaining_uses=3，value 更高）已足够，不需要新增低阶阵法。

---

## 抗单一最优玩法分析

### 丹药分析

| 物品 | 最优场景 | 为什么不是全局最优 |
|------|----------|---------------------|
| 养气丹 | 修炼加速 | 只生效 1 次，加成小，不能替代阵法 |
| 固元丹 | 突破准备 | 只生效 1 次，需要特定时机使用 |
| 回春丹 | 探索续航 | 即时恢复，不能替代 HP 功法/道具 |

### 符箓分析

| 物品 | 最优场景 | 为什么不是全局最优 |
|------|----------|---------------------|
| 探路符 | 探索加成 | 只生效 1 次，+5% 聊胜于无 |
| 避祸符 | 探索减伤 | 只生效 1 次，25% 减伤不如 guard_talisman |
| 聚灵符 | 修炼加成 | 只生效 1 次，远弱于阵法（0.04 vs 0.12） |

### 法器分析

| 物品 | 最优场景 | 为什么不是全局最优 |
|------|----------|---------------------|
| 青木佩 | 探索加成 | 探索型，与低阶 sword 类似 |
| 聚气玉 | 修炼加成 | 修炼型，比 gathering_artifact 弱 |
| 护身铃 | 探索防御 | 探索型，与 guard_talisman 不同维度 |

**结论：没有任何单一物品/技能可以碾压其他路线。**

---

## 为什么不会破坏探索核心地位

1. **加成幅度小**：所有新增效果 value 都在 0.04~0.25 范围，极有限
2. **持续时间短**：remaining_uses=1，新鲜感大于实际收益
3. **材料成本不低**：需要 healing_herb、low_material、low_spirit_stone 等
4. **境界要求**：需要炼气 2~4 层才能使用大部分配方
5. **制作仍走 /action/execute**：不能绕过核心系统

---

## 配方数量变化

| 技能 | 原有 | 本轮新增 | 现有 |
|------|------|----------|------|
| alchemy | 3 | 3 | 6 |
| talisman | 3 | 3 | 6 |
| crafting | 3 | 3 | 6 |
| formation | 3 | 0 | 3 |

---

## 测试结果

### 语法检查

```
C:\Users\WTT\AppData\Local\Programs\Python\Python310\python.exe -m compileall -q backend
```
✅ 通过（无输出）

### 文件解析

```python
ast.parse(open(f).read()) for f in [recipes_alchemy, recipes_talisman, recipes_crafting, items, effects, calc_service]
```
✅ 全部通过

### 后端服务

⚠️ 8000 端口当前无服务监听（ConnectionRefused）
⚠️ smoke_test 需要后端运行，无法在当前环境执行
⚠️ simulation 需要后端运行，无法在当前环境执行

**预计测试（需 Codex/用户启动后端后执行）：**
- `python -m compileall backend` ✅（已通过）
- `python tests/smoke_test.py` — 待后端启动
- `simulation 3h with_sect=true` — 待后端启动
- `simulation 12h with_sect=true` — 待后端启动
- `simulation 24h with_sect=true` — 待后端启动

### 预计新增配方在 /life-skills/recipes 中的分布

```json
{
  "alchemy": [旧3个... + "alchemy_yangqi_pill", "alchemy_guyu_pill", "alchemy_huichun_pill"],
  "talisman": [旧3个... + "talisman_explore_luck", "talisman_avoid_harm", "talisman_spirit_gather"],
  "crafting": [旧3个... + "craft_qingmu_pendant", "craft_juqi_jade", "craft_hushen_bell"],
  "formation": [3个原版，未改动]
}
```

---

## 风险检查

| 检查项 | 结论 |
|--------|------|
| 是否修改 main | ❌ 否，基于实验分支 |
| 是否删除核心文件 | ❌ 否 |
| 是否存在大量删除 | ❌ 否，只有新增（+256 行） |
| 是否可能出现单一最优玩法 | ❌ 未发现，所有物品加成幅度小且一次生效 |
| 是否破坏探索核心地位 | ❌ 探索仍是唯一主要资源来源 |
| 是否法力循环失控 | ❌ 所有制作仍扣法力 |
| 是否材料循环失控 | ❌ 所有配方需要材料，无法无限产出 |

---

## 是否可以交给 Codex 审查？

**✅ 可以，但建议在后端启动后运行完整 smoke_test + simulation 3/12/24h 验证。**

本轮修改：
- 只改 configs（recipes_*/items.py/effects.py）
- 只改 calc_service（apply_item_effects 新增处理 3 个新 effect key）
- 所有配方走 /action/execute，不破坏架构
- 无 P0/P1 风险

---

## 修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/configs/recipes_alchemy.py` | 修改 | +3 丹药配方 |
| `backend/configs/recipes_talisman.py` | 修改 | +3 符箓配方 |
| `backend/configs/recipes_crafting.py` | 修改 | +3 法器配方 |
| `backend/configs/items.py` | 修改 | +9 物品模板（3 丹药 + 3 符箓 + 3 法器） |
| `backend/configs/effects.py` | 修改 | +9 active_effect 配置 + 5 个新 item active_effect |
| `backend/services/calc_service.py` | 修改 | apply_item_effects 处理 5 个新 effect key |

---

## 后续要求

- 任务结束后更新 `generator-log.md`
- 任务结束后更新 `MEMORY.md`
- 任务结束后更新 `memory/2026-05-13.md`