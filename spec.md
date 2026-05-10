# 修仙游戏项目开发里程碑

## 当前状态

- 当前阶段：第三阶段，玩法成型 + 节奏控制 + 宗门系统
- 宗门系统第一版已完成
- 已有系统：
  - 探索 / 掉落 / 机缘
  - 功法成长
  - 法宝强化
  - 瓶颈突破
  - 固定 81 格背包
  - 统一行为接口 `/action/execute`
  - simulation 模拟系统
  - 新手任务系统
  - 宗门系统
- 所有核心逻辑必须在后端
- 所有数值必须进入 `configs` 或 `calc_service`
- 所有行为必须走 `/action/execute`
- 不允许出现“单一最优玩法”
- 探索必须仍然是核心资源来源
- 法力是唯一行动资源
- 气运、心魔等隐藏属性不得直接显示到前端

---

# 本轮目标：v2.0 生活技能系统

本轮目标是实现修仙世界中的四类非战斗技能：

1. 炼丹
2. 符箓
3. 炼器
4. 阵法

核心定位：

生活技能不是独立刷资源系统，而是：

```text
探索获得材料
→ 生活技能加工转化
→ 辅助修炼 / 探索 / 突破 / 宗门任务
→ 再回到探索和成长循环

生活技能必须是“资源转化器”，不能成为“资源生产器”。

本轮重点

请按阶段逐步实现，不要一次性做完所有复杂内容。

当前优先级：

先实现统一配方系统
再实现炼丹
再实现符箓
再实现炼器
最后实现阵法基础版
每个阶段都必须更新测试和 simulation
v2.0 总体设计原则
必须遵守
所有核心逻辑在后端
所有数值写入 configs
所有计算集中到 calc_service
所有生产行为走 /action/execute
所有产物进入背包系统
背包满时必须失败并返回明确错误
所有行为写入 game_logs 或 action_records
必须兼容 simulation
必须通过 smoke_test
禁止事项
禁止在前端写核心逻辑
禁止硬编码配方和奖励
禁止一次做交易、拍卖、玩家市场
禁止做复杂随机极品系统
禁止生活技能替代探索
禁止炼丹无限续航
禁止炼器产物全面碾压探索掉落
禁止阵法成为永久无成本加成
阶段 1：统一配方系统
目标

建立生活技能共用的配方系统，支持炼丹、符箓、炼器、阵法复用。

新增配置

建议新增：

backend/configs/recipes.py

或按类型拆分：

backend/configs/recipes_alchemy.py
backend/configs/recipes_talisman.py
backend/configs/recipes_crafting.py
backend/configs/recipes_formation.py
配方字段

每个 recipe 至少包含：

{
    "id": "qi_recovery_pill_1",
    "name": "回气丹",
    "skill_type": "alchemy",
    "required_realm": "qi_refining",
    "required_items": {
        "spirit_grass": 2,
        "clear_dew": 1
    },
    "mana_cost": 10,
    "output_item_id": "qi_recovery_pill",
    "output_count": 1,
    "success_rate": 1.0,
    "required_sect": None,
    "required_faction": None,
    "required_reputation": 0,
    "required_contribution": 0
}
后端要求

新增统一服务：

backend/services/life_skill_service.py

建议包含：

get_available_recipes
execute_recipe
validate_recipe
consume_materials
create_output_item
record_life_skill_log
action_type

通过 /action/execute 新增：

alchemy
talisman
crafting
formation

请求参数：

{
  "action_type": "alchemy",
  "payload": {
    "recipe_id": "qi_recovery_pill_1"
  }
}
测试要求
材料不足时失败
法力不足时失败
背包满时失败
成功时扣材料、扣法力、生成物品
写入日志
smoke_test 通过
阶段 2：炼丹系统
目标

炼丹用于制造消耗品，辅助修炼、探索、突破。

初版丹药

建议先做：

回气丹
恢复少量法力
限制使用频率，避免无限续航
聚气丹
短时间提升修炼收益
不允许超过探索收益价值
筑基丹
作为突破辅助材料
不能直接保证突破成功
要求
丹药必须是消耗品
使用丹药也必须走 /action/execute
丹药效果写入后端
丹药不能无限叠加
高价值丹药材料必须来自探索或宗门商店
必须检查
是否出现只炼丹最优
是否出现回气丹无限续航
是否出现聚气丹让纯修炼重新最优
阶段 3：符箓系统
目标

符箓是一次性消耗品，主要强化探索和风险控制。

初版符箓

建议先做：

探查符
提高秘境 / 机缘触发概率
护身符
降低探索负面事件概率
速行符
降低一次探索法力消耗
要求
符箓必须是一次性消耗品
不能永久加成
不能叠加到破坏探索节奏
使用符箓必须写入日志
simulation 必须能测试符箓收益
必须检查
符箓是否让探索变得无脑
速行符是否导致无限探索
探查符是否让秘境产出过高
阶段 4：炼器系统
目标

炼器用于制造基础法器、探索辅助物、傀儡雏形。

初版产物

建议先做：

下品法剑
提升战斗能力
聚灵法器
提升少量修炼效率
探索傀儡
提高少量掉落概率或降低探索风险
要求
炼器产物进入装备 / 法宝 / 物品体系
不要新增复杂极品词条
不要做本命法宝完整系统
本命法宝只做字段和设计预留
炼器装备不能全面强于探索掉落
必须检查
是否出现只炼器最优
炼器装备是否碾压掉落装备
探索傀儡是否让探索收益失控
阶段 5：阵法系统基础版
目标

阵法用于提供有限时间、有限场景的辅助效果。

初版阵法

建议先做：

聚灵阵
提升一定时间内修炼效率
防护阵
降低探索或突破风险
引灵阵
增加部分资源获取概率
要求
阵法必须有持续时间或使用次数
阵法必须消耗材料
阵法不能永久生效
阵法不能和丹药、符箓无限叠加
阵法效果必须后端计算
必须检查
聚灵阵是否让纯修炼最优
引灵阵是否让探索收益爆炸
阵法是否成为必刷内容
宗门系统联动

生活技能需要与宗门系统轻度联动。

可做内容
宗门任务新增：
炼丹任务
制符任务
炼器任务
布阵任务
宗门商店新增：
配方
稀有材料
基础丹炉 / 符纸 / 器胚 / 阵旗
宗门贡献可解锁：
高级配方
阵营特色配方
阵营差异预留
正道：丹药、法剑、聚灵阵
魔道：攻击符、血炼器、风险高收益阵法
鬼道：傀儡、阴魂符、幽冥阵
佛道：护身符、防护阵、净心丹

本阶段只做基础差异，不做复杂阵营战争。

simulation 要求

每个阶段完成后都必须运行：

/dev/simulation?hours=3&with_sect=true
/dev/simulation?hours=12&with_sect=true
/dev/simulation?hours=24&with_sect=true

simulation 输出必须包含：

探索占比
修炼占比
宗门任务占比
炼丹次数
符箓使用次数
炼器次数
阵法使用次数
生活技能收益占比
是否出现单一最优玩法
warnings
每轮研发 Agent 工作要求

研发 Agent 每次只做一个小阶段。

每次工作前必须阅读：

SPEC.md
feedback/*.md
generator-log.md

每次完成后必须生成或更新：

generator-log.md

内容包括：

本轮完成了什么
修改了哪些文件
新增了哪些接口 / action_type
测试结果
simulation 结果
发现的问题
下一轮建议

必须执行：

python -m compileall -q main.py backend tests
python tests/smoke_test.py
每轮产品/测试 Agent 工作要求

产品/测试 Agent 不直接写代码。

每轮必须检查：

是否偏离 SPEC.md
是否破坏核心循环
是否出现单一最优玩法
是否有硬编码
是否有前端逻辑越权
是否有测试缺失
simulation 是否可信
是否需要调整数值或拆小任务

每轮生成：

feedback/YYYYMMDD_round_x.md

内容包括：

本轮验收结论
发现的问题
必须修复的问题
可延后问题
下一轮研发任务
是否允许进入下一阶段
分支开发规则

建议新建分支：

git checkout -b feature/life-skills-v2

每个小阶段单独提交：

v2.0.1 recipe foundation
v2.0.2 alchemy system
v2.0.3 talisman system
v2.0.4 crafting system
v2.0.5 formation system
v2.0.6 simulation balance tuning

禁止一次性大提交。

当前最近任务
下一轮研发 Agent 请优先完成
v2.0.1 统一配方系统基础版

只做：

新增 recipes 配置结构
新增 life_skill_service
接入 /action/execute
实现 alchemy / talisman / crafting / formation 的统一执行入口
先放入少量测试配方
更新 smoke_test
更新 simulation 基础字段

不要急着完整做炼丹、符箓、炼器、阵法效果。

本轮重点是：

先把生活技能的“统一生产骨架”搭好。

