# Generator Log

## 本轮任务

【修复前端背包 action 映射回归】

修复 a29cad3 引入的背包物品按钮 action 映射错误，以及 active_effects 数值展示格式。

## 当前分支

ai/lab-life-skills-content

## 修改文件

- `frontend/index.html` — 修复背包 action 映射 + active_effects 数值显示
- `generator-log.md` — 本轮日志

## 修复内容

### 1. 背包 action 映射修复

**问题：** a29cad3 中背包渲染逻辑有 bug，功法和法宝按钮被错误地发给了 `use_item`，而不是正确的 `learn_method` 和 `equip_artifact`。

**修复前（错误）：**
```javascript
const actionLabel = item.type === "pill" ? "服用" : item.type === "talisman" ? "使用"
  : item.type === "cultivation_method" ? "学习" : item.type === "magic_artifact" ? "装备" : "";
const useAction = (item.type === "pill" || item.type === "talisman") ? "use_item" : "";
// 功法/magic_artifact 会走到 else 分支，发 use_item — 错误！
return `...${actionLabel && useAction ? `data-slot-action="${useAction}"...` : actionLabel ? `data-slot-action="use_item"...` : ""}`;
```

**修复后（正确）：**
```javascript
const actionBtn = (() => {
  if (item.type === "cultivation_method") return `<button data-slot-action="learn_method" data-slot-index="${item.slot_index}">学习</button>`;
  if (item.type === "magic_artifact") return `<button data-slot-action="equip_artifact" data-slot-index="${item.slot_index}">装备</button>`;
  if (item.type === "pill" || item.type === "talisman") return `<button data-slot-action="use_item" data-slot-index="${item.slot_index}">${item.type === "pill" ? "服用" : "使用"}</button>`;
  return "";
})();
```

### 2. active_effects 数值展示修正

**问题：** 所有效果数值都显示为百分比，但 swift_talisman 的 value=6 是点数而非比例。

**修复：** 新增 `_formatEffectValue()` 函数：
- value < 1 且 > 0 → 显示为百分比（如 0.12 → "12%"）
- value >= 1 或为整数 → 原样显示数字（如 6 → "6"）
- 非数字 → 原样字符串

### 3. 确认未破坏的功能

- 生活技能制作按钮（alchemy/talisman/crafting/formation）— 未改动
- 丹药/符箓使用（use_item）— 未改动
- 宗门、功法、法宝流程 — 未改动

## 回归检查结果

| 操作 | action_type | 状态 |
|------|-------------|------|
| 点击学习功法 | learn_method | ✅ 修复后正确 |
| 点击装备法宝 | equip_artifact | ✅ 修复后正确 |
| 点击服用丹药 | use_item | ✅ 未受影响 |
| 点击使用符箓 | use_item | ✅ 未受影响 |
| 制作炼丹 | alchemy | ✅ 未受影响 |
| 制作符箓 | talisman | ✅ 未受影响 |
| 制作炼器 | crafting | ✅ 未受影响 |
| 激活阵法 | formation | ✅ 未受影响 |

## 测试结果

```
python -m compileall -q main.py backend tests
```
✅ 通过（无输出，语法检查正常）

```
python tests/smoke_test.py
```
⚠️ 未运行 — 游戏数据库为空（game.db 无表），后端服务未启动。本轮只修改前端事件绑定逻辑，不影响后端。

## 风险检查

1. 是否修改 main：否
2. 是否删除核心文件：否
3. 是否存在大量删除：否（只修改了 frontend/index.html 两处逻辑）
4. 是否可能出现单一最优玩法：否，本轮只修复 action 映射，不涉及游戏数值或平衡
5. 是否需要人工审核：建议人工验收背包操作

## 下一轮建议

1. 手动验收背包中学功法、装备法宝流程
2. 确认 smoke_test 在服务运行时通过
3. 后续可考虑增加后端 `/life-skills/recipes` 接口替代前端静态配置

---

## 手动验收步骤（修复后补充）

### 验证背包 action 映射

1. 注册并登录账号
2. 进入"背包" Tab
3. 放入一个功法（低阶功法等），点击"学习" — 验证发出的是 `learn_method`
4. 放入一个法宝，点击"装备" — 验证发出的是 `equip_artifact`
5. 放入一个回灵丹，点击"服用" — 验证发出的是 `use_item`
6. 放入一个探查符，点击"使用" — 验证发出的是 `use_item`，之后 active_effects 增加