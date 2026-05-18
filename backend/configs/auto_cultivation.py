"""
自动修行配置
"""

# 最大离线累计时间（小时）
MAX_OFFLINE_HOURS = 8

# 每轮结算周期（分钟）
SETTLE_INTERVAL_MINUTES = 10

# 自动历练基础掉落表（按品质分级）
# 第一版：复用现有材料/丹药/灵石，通过品质权重控制分布
AUTO_DROP_TABLE = [
    # 凡品 common — 高概率（使用不可堆叠的 low_artifact 填满背包）
    {"code": "low_artifact", "rarity": "凡品", "weight": 35, "quantity_range": [1, 1]},
    {"code": "healing_herb", "rarity": "凡品", "weight": 20, "quantity_range": [1, 3]},
    {"code": "low_material", "rarity": "凡品", "weight": 15, "quantity_range": [1, 3]},
    # 下品 low — 中高概率
    {"code": "mana_pill", "rarity": "下品", "weight": 15, "quantity_range": [1, 2]},
    {"code": "healing_pill", "rarity": "下品", "weight": 12, "quantity_range": [1, 2]},
    {"code": "qi_powder", "rarity": "下品", "weight": 10, "quantity_range": [1, 2]},
    # 中品 middle — 中低概率
    {"code": "low_method", "rarity": "中品", "weight": 8, "quantity_range": [1, 1]},
    {"code": "low_spirit_stone", "rarity": "中品", "weight": 6, "quantity_range": [10, 20]},
    # 上品 high — 低概率
    {"code": "foundation_pill", "rarity": "上品", "weight": 5, "quantity_range": [1, 1]},
    {"code": "mid_material", "rarity": "上品", "weight": 4, "quantity_range": [1, 2]},
    # 极品 rare — 极低概率
    {"code": "core_pill", "rarity": "极品", "weight": 3, "quantity_range": [1, 1]},
    {"code": "mid_artifact", "rarity": "极品", "weight": 2, "quantity_range": [1, 1]},
    # 妖丹（特殊物品，不可堆叠）
    {"code": "beast_core", "rarity": "凡品", "weight": 4, "quantity_range": [1, 1]},
    # 残破玉简（特殊物品，不可堆叠）
    {"code": "broken_jade_slip", "rarity": "下品", "weight": 3, "quantity_range": [1, 1]},
]

# 策略配置
STRATEGIES = {
    "steady": {
        "name": "稳健修行",
        "description": "法力充足再外出，气血稍低即回洞府，风险较低。",
        "mana_threshold_percent": 80,
        "hp_threshold_percent": 70,
        "reward_multiplier": 0.8,
        "injury_multiplier": 0.6,
    },
    "balanced": {
        "name": "均衡修行",
        "description": "收益与风险适中，适合日常修行。",
        "mana_threshold_percent": 60,
        "hp_threshold_percent": 50,
        "reward_multiplier": 1.0,
        "injury_multiplier": 1.0,
    },
    "aggressive": {
        "name": "激进历练",
        "description": "更频繁外出，收益更高，但更容易受伤。",
        "mana_threshold_percent": 40,
        "hp_threshold_percent": 30,
        "reward_multiplier": 1.3,
        "injury_multiplier": 1.5,
    },
}

# 自动状态名称（中文）
AUTO_STATE_NAMES = {
    "meditating": "洞府打坐",
    "adventuring": "自行历练",
    "resting": "洞府休整",
    "paused": "等待处理",
    "injured": "重伤暂停",
}

# 打坐恢复法力量
MEDITATE_MANA_RECOVER = 30

# 打坐获得修为量（每次）
MEDITATE_CULTIVATION_GAIN = 8

# 休整恢复气血量（每次）
REST_HEAL_AMOUNT = 40

# 历练消耗法力
ADVENTURE_MANA_COST = 18

# 历练基础修为获得
ADVENTURE_CULTIVATION_GAIN_MIN = 4
ADVENTURE_CULTIVATION_GAIN_MAX = 16

# 历练基础灵石获得
ADVENTURE_STONES_MIN = 18
ADVENTURE_STONES_MAX = 68

# 历练战斗伤害基础范围
BATTLE_DAMAGE_MIN = 4
BATTLE_DAMAGE_MAX = 18