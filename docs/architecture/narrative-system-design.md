# 叙事系统架构设计 — P0 需求

**文档版本**: v1.0
**创建日期**: 2026-06-18
**架构师**: 齐活林（主理人代行，原架构师未响应）
**基于PRD**: `docs/prd/narrative-content-v1.md`
**开发分支**: `feature/narrative-content-v1`

---

## 一、实现方案 + 框架选型

### 1.1 叙事文本存储方案

**决策：静态配置文件（JSON）+ 后端内存缓存**

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 数据库存储 | 热更新方便 | 增加数据库压力，增加复杂度 | ❌ 不选 |
| Python配置文件（py） | 无需解析，直接import | 编辑需重启后端 | ✅ **选中** |
| JSON静态文件 | 易编辑，易版本控制 | 需解析 | ✅ 备选 |

**最终方案**：使用 Python 配置文件（`backend/configs/narrative_texts.py`），以 dict 结构存储所有叙事文本，后端 import 后直接使用。无需解析，支持中文，编辑后重启后端即可生效。

### 1.2 前端叙事面板方案

**决策：直接DOM操作（不引入框架）**

前端是单文件 HTML（`frontend/index.html`），已使用原生 JS。叙事面板直接以 DOM 操作方式插入，不引入 React/Vue。

**展示方式**：
- 弹窗叙事（普通事件）：在现有UI上层叠加半透明遮罩 + 叙事卡片
- 全屏叙事（重要事件/开局）：暂时隐藏主UI，全屏展示

### 1.3 后端 → 前端叙事文本传递方案

**决策：Action API 响应中新增 `narrative` 字段**

所有动作执行（`/action/execute` POST）的响应 JSON 中，新增可选字段 `narrative: str | None`。

- 有叙事文本时：`{"success": true, "message": "...", "narrative": "你在一处石缝中..."}`
- 无叙事文本时：字段不返回（或返回 `null`）

前端检查响应中是否有 `narrative` 字段，有则展示叙事面板。

---

## 二、文件列表及相对路径

### 新增文件

| 文件路径 | 说明 | 优先级 |
|-----------|------|--------|
| `backend/configs/narrative_texts.py` | 所有P0叙事文本集中配置 | P0 |
| `tests/test_narrative_texts.py` | 叙事文本格式校验测试 | P0 |

### 修改文件

| 文件路径 | 修改内容 | 优先级 |
|-----------|-----------|--------|
| `backend/configs/events.py` | 所有事件新增 `narrative` 字段 | P0 |
| `backend/services/action_service.py` | 所有动作处理器返回 `narrative` 字段 | P0 |
| `frontend/index.html` | 新增叙事面板CSS + JS + HTML | P0 |
| `docs/review/feature-narrative-content-v1-handoff.md` | 本分支交付文档（工程师完成后创建） | P0 |

---

## 三、数据结构和接口

### 3.1 事件配置数据结构（修改后）

```python
# backend/configs/events.py

EXPLORE_EVENTS = [
    {
        "code": "spirit_stone_cache",
        "name": "石缝中的灵光",          # 修改后的叙事性名称
        "type": "reward_spirit_stones",
        "weight": 28,
        "min_realm": "炼气一层",
        "max_realm": "化神后期",
        "conditions": {},
        "rewards": {"spirit_stones": [18, 68]},
        "risks": {},
        "narrative": "你在一处石缝中，察觉到微弱的灵气波动。\n\n拨开碎石，发现几块下品灵石嵌在石壁里，像是有人曾经在这里修炼过，遗落了这些。",  # 新增：2-4行叙事描述
    },
    # ... 其他事件类似修改
]
```

### 3.2 动作响应接口（新增字段）

```python
# 后端 /action/execute 响应格式（新增 narrative 字段）

# 有叙事文本时：
{
    "success": true,
    "message": "打坐修炼消耗 12 点法力，修为增加 15",
    "narrative": "三个时辰过去了，你才发现天色已暗。体内的灵气比晨起时凝实了一些，但距离突破还差得很远。\n\n你揉了揉发麻的双腿，心想：这样下去，要到什么时候才能……",  # 可选，触发时返回
    "results": {...}
}

# 无叙事文本时（字段不返回）：
{
    "success": true,
    "message": "...",
    "results": {...}
}
```

### 3.3 前端叙事面板接口（JS函数签名）

```javascript
/**
 * 展示叙事面板
 * @param {string} text - 叙事文本（支持 \n 换行）
 * @param {string} mode - 展示模式："popup"（弹窗）| "fullscreen"（全屏）
 * @param {function} onComplete - 玩家点击"继续"后的回调
 */
function showNarrativePanel(text, mode = "popup", onComplete = null) { ... }

/**
 * 打字机效果展示文本
 * @param {HTMLElement} container - 文本容器元素
 * @param {string} text - 完整文本
 * @param {number} speed - 每字间隔毫秒（默认50）
 * @param {function} onComplete - 打字结束后的回调
 */
function typewriterEffect(container, text, speed = 50, onComplete = null) { ... }
```

---

## 四、程序调用流程

### 4.1 探索事件叙事流程

```
玩家点击"探索" → 前端 POST /action/execute {action_type: "explore"}
              → 后端 action_service.py _explore()
              → 根据权重随机选择事件（events.py EXPLORE_EVENTS）
              → 读取事件的 narrative 字段
              → 返回 {success, message, narrative, results}
              → 前端收到响应
              → 检查是否有 narrative 字段
              → 有：调用 showNarrativePanel(narrative, "popup")
              → 玩家点击"继续" → 正常展示 results（奖励）
              → 无：直接展示 results
```

### 4.2 修炼叙事触发流程（随机）

```
玩家点击"修炼" → 前端 POST /action/execute {action_type: "train"}
              → 后端 action_service.py _train()
              → 30%概率触发叙事文本（从 narrative_texts.py 读取）
              → 返回 {success, message, narrative, results}
              → 前端展示叙事面板（如有）
              → 继续正常流程
```

---

## 五、任务列表（按实现顺序排列）

> **依赖说明**：Task N 依赖 Task M 表示 Task N 的代码需要引用 Task M 中定义的结构/函数。

| Task # | 任务描述 | 修改文件 | 依赖 | 预估时间 |
|---------|-----------|-----------|------|----------|
| **Task 1** | 修改 events.py，为所有8个事件新增 `narrative` 字段（使用叙事性文本替换功能化描述） | `backend/configs/events.py` | 无 | 1小时 |
| **Task 2** | 创建 narrative_texts.py，定义修炼/突破的随机叙事文本池 | `backend/configs/narrative_texts.py` | 无 | 1小时 |
| **Task 3** | 修改 action_service.py，在所有动作处理器中返回 `narrative` 字段（从 events.py 或 narrative_texts.py 读取） | `backend/services/action_service.py` | Task 1, Task 2 | 2小时 |
| **Task 4** | 前端新增叙事面板CSS（弹窗样式 + 全屏样式） | `frontend/index.html` (CSS部分) | 无 | 1小时 |
| **Task 5** | 前端新增叙事面板JS（`showNarrativePanel` + `typewriterEffect`） | `frontend/index.html` (JS部分) | Task 4 | 1.5小时 |
| **Task 6** | 前端修改 `/action/execute` 的响应处理，检测到 `narrative` 字段时调用叙事面板 | `frontend/index.html` (JS部分) | Task 3, Task 5 | 1小时 |
| **Task 7** | 编写叙事系统测试（校验 events.py 的 narrative 字段格式、action_service 返回格式） | `tests/test_narrative_texts.py` | Task 1, Task 3 | 1小时 |

**总预估时间**：8.5小时

---

## 六、依赖包列表

**无新增依赖** — 所有功能使用现有框架（FastAPI + SQLAlchemy + 原生JS）即可实现。

---

## 七、共享知识（跨文件约定）

### 7.1 叙事文本格式约定

1. **行长限制**：每行不超过40个汉字（或60个英文字符），确保移动端显示正常
2. **换行符**：使用 `\n\n` 表示段落分隔，`\n` 表示普通换行
3. **字数限制**：
   - 事件叙事（events.py）：80-160字（2-4行）
   - 修炼叙事（narrative_texts.py）：60-120字（2-3行）
   - 突破叙事（后续P1）：120-300字（4-8行）
4. **禁止内容**：
   - 不允许出现具体数值（如"攻击+12"），改为描述性语言
   - 不允许打破第四面墙（如"点击按钮继续"）

### 7.2 打字机效果实现约定

```javascript
// 前端实现打字机效果的标准方式
function typewriterEffect(container, text, speed = 50, onComplete = null) {
    let index = 0;
    container.textContent = '';  // 清空容器
    
    function type() {
        if (index < text.length) {
            // 支持 \n 换行
            if (text[index] === '\n') {
                container.appendChild(document.createElement('br'));
            } else {
                container.textContent += text[index];
            }
            index++;
            setTimeout(type, speed);
        } else {
            // 打字完成，显示"继续"按钮
            if (onComplete) onComplete();
        }
    }
    
    type();
}
```

### 7.3 错误兜底方案

**原则：叙事文本是"增强体验"，不能因为叙事文本缺失导致功能无法使用。**

1. **events.py 中某个事件缺少 `narrative` 字段**：
   - 后端返回时不包含 `narrative` 字段
   - 前端正常展示 results（奖励），不展示叙事面板
   
2. **narrative_texts.py 中某个境界的叙事文本池为空**：
   - 后端不返回 `narrative` 字段
   - 前端正常展示 results

3. **前端 `showNarrativePanel` 函数报错**：
   - 捕获异常，console.error 输出错误
   - 继续正常展示 results

---

## 八、待明确事项

| # | 问题 | 需要澄清的人 | 状态 |
|---|------|--------------|------|
| 1 | 修炼叙事的30%触发概率是否合适？是否需要按境界调整概率？ | 主策划（用户） | 🔄 待确认 |
| 2 | 叙事面板的"继续"按钮文案：使用"继续"还是"可知矣"？ | 主策划（用户） | 🔄 待确认 |
| 3 | 是否需要在设置中增加"关闭叙事描述"选项？ | 主策划（用户） | 🔄 待确认 |

**说明**：以上待确认问题不影响开发，工程师可以先按默认值实现（30%概率、"继续"按钮、暂不增加关闭选项），后续根据用户反馈调整。

---

## 九、验收标准（架构视角）

### 9.1 后端验收标准

- [ ] `events.py` 所有8个事件都已新增 `narrative` 字段，且字段值为非空字符串
- [ ] `action_service.py` 所有动作处理器（`_train`, `_explore`, `_breakthrough`）在适当情况下返回 `narrative` 字段
- [ ] `narrative` 字段内容符合格式约定（行长、换行、字数）
- [ ] 后端所有现有单元测试仍然通过（叙事改造不破坏现有功能）

### 9.2 前端验收标准

- [ ] 叙事面板CSS已实现，样式符合PRD中的设计规范（半透明遮罩、叙事卡片样式）
- [ ] 打字机效果流畅，速度可配置（默认50ms/字）
- [ ] 玩家可以点击"继续"按钮跳过打字过程（提前完成）
- [ ] 叙事面板展示期间，主UI操作被禁用（避免重复触发）

### 9.3 集成验收标准

- [ ] 玩家点击"探索" → 触发事件 → 先展示叙事面板 → 点击"继续" → 展示奖励
- [ ] 玩家点击"修炼" → 30%概率触发叙事面板 → 展示修炼叙事文本
- [ ] 叙事文本展示期间，玩家可以按空格键跳过打字过程

---

## 十、实施顺序建议

```
Day 1 (今天):
  ✅ Task 1: 修改 events.py（工程师）
  ✅ Task 2: 创建 narrative_texts.py（工程师）
  ✅ Task 3: 修改 action_service.py（工程师）

Day 2:
  🔲 Task 4: 前端叙事面板CSS（工程师）
  🔲 Task 5: 前端叙事面板JS（工程师）
  🔲 Task 6: 前端响应处理改造（工程师）

Day 3:
  🔲 Task 7: 编写测试（QA）
  🔲 联调测试（QA + 工程师）
  🔲 修复Bug（工程师）

Day 4:
  🔲 提交 PR + 等待Codex复验
```

---

**文档结束**

> **下一步行动**：
> 1. 工程师（寇豆码）按照 Task 1 → Task 7 的顺序实现代码
> 2. QA（严过关）在工程师完成后运行测试并报告结果
> 3. 主理人（齐活林）保障团队持续工作，每30分钟检查进度
