"""
修仙游戏数值计算服务
====================
核心设计理念：
1. 五行克制：金克木、木克土、土克水、水克火、火克金
2. 指数增长：法宝/功法数值随等阶指数级增长
3. 法力消耗：与玩家法力上限挂钩，体现"法力深厚"的优势
4. 通天灵宝：唯一性机制，全服仅存一件
"""

from enum import Enum
from typing import Optional
import math


# ==================== 五行克制体系 ====================

class Element(Enum):
    """五行属性"""
    METAL = "金"      # 金
    WOOD = "木"       # 木
    WATER = "水"      # 水
    FIRE = "火"       # 火
    EARTH = "土"      # 土
    THUNDER = "雷"    # 雷（特殊，无克制）
    ICE = "冰"        # 冰（特殊，无克制）
    WIND = "风"       # 风（特殊，无克制）
    YIN = "阴"        # 阴（特殊）
    YANG = "阳"       # 阳（特殊）
    NEUTRAL = "无"    # 无属性


# 五行克制关系：攻击方属性 -> 被克制属性 -> 伤害加成
ELEMENT_RESTRAINT = {
    Element.METAL: {Element.WOOD: 0.20},      # 金克木：+20%伤害
    Element.WOOD: {Element.EARTH: 0.20},      # 木克土：+20%伤害
    Element.EARTH: {Element.WATER: 0.20},     # 土克水：+20%伤害
    Element.WATER: {Element.FIRE: 0.20},      # 水克火：+20%伤害
    Element.FIRE: {Element.METAL: 0.20},      # 火克金：+20%伤害
}

# 五行被克制关系（反向）
ELEMENT_WEAKNESS = {
    Element.METAL: {Element.FIRE: -0.15},     # 金被火克：-15%伤害
    Element.WOOD: {Element.METAL: -0.15},     # 木被金克：-15%伤害
    Element.EARTH: {Element.WOOD: -0.15},     # 土被木克：-15%伤害
    Element.WATER: {Element.EARTH: -0.15},    # 水被土克：-15%伤害
    Element.FIRE: {Element.WATER: -0.15},     # 火被水克：-15%伤害
}


def get_element_multiplier(attacker_element: Element, defender_element: Element) -> float:
    """
    计算五行克制伤害倍率
    
    Args:
        attacker_element: 攻击方属性
        defender_element: 防御方属性
    
    Returns:
        伤害倍率（1.0为无加成，1.2为克制，0.85为被克制）
    """
    base_multiplier = 1.0
    
    # 检查克制关系
    if attacker_element in ELEMENT_RESTRAINT:
        if defender_element in ELEMENT_RESTRAINT[attacker_element]:
            base_multiplier += ELEMENT_RESTRAINT[attacker_element][defender_element]
    
    # 检查被克制关系
    if attacker_element in ELEMENT_WEAKNESS:
        if defender_element in ELEMENT_WEAKNESS[attacker_element]:
            base_multiplier += ELEMENT_WEAKNESS[attacker_element][defender_element]
    
    return base_multiplier


# ==================== 法宝等阶体系 ====================

class ArtifactTier(Enum):
    """法宝等阶"""
    LOW_MAGIC = "低阶法器"
    MID_MAGIC = "中阶法器"
    HIGH_MAGIC = "高阶法器"
    TOP_MAGIC = "顶阶法器"
    LOW_ARTIFACT = "低阶法宝"
    MID_ARTIFACT = "中阶法宝"
    HIGH_ARTIFACT = "高阶法宝"
    TOP_ARTIFACT = "顶阶法宝"
    LOW_TREASURE = "低阶古宝"
    MID_TREASURE = "中阶古宝"
    HIGH_TREASURE = "高阶古宝"
    TOP_TREASURE = "顶阶古宝"
    LOW_SPIRIT = "低阶灵宝"
    MID_SPIRIT = "中阶灵宝"
    HIGH_SPIRIT = "高阶灵宝"
    TOP_SPIRIT = "顶阶灵宝"
    SUPREME = "通天灵宝"


# 等阶系数（指数增长模型）
# 设计理念：每提升一个大等阶，数值翻倍；每提升一个小等阶，数值增长50%
TIER_MULTIPLIER = {
    ArtifactTier.LOW_MAGIC: 1.0,           # 基准
    ArtifactTier.MID_MAGIC: 1.5,           # +50%
    ArtifactTier.HIGH_MAGIC: 2.25,         # +50%
    ArtifactTier.TOP_MAGIC: 3.375,         # +50%
    ArtifactTier.LOW_ARTIFACT: 6.75,       # x2（大等阶跃升）
    ArtifactTier.MID_ARTIFACT: 10.125,     # +50%
    ArtifactTier.HIGH_ARTIFACT: 15.1875,   # +50%
    ArtifactTier.TOP_ARTIFACT: 22.78125,   # +50%
    ArtifactTier.LOW_TREASURE: 45.5625,    # x2
    ArtifactTier.MID_TREASURE: 68.34375,   # +50%
    ArtifactTier.HIGH_TREASURE: 102.515625,# +50%
    ArtifactTier.TOP_TREASURE: 153.7734375,# +50%
    ArtifactTier.LOW_SPIRIT: 307.546875,   # x2
    ArtifactTier.MID_SPIRIT: 461.3203125,  # +50%
    ArtifactTier.HIGH_SPIRIT: 691.98046875,# +50%
    ArtifactTier.TOP_SPIRIT: 1037.970703125,# +50%
    ArtifactTier.SUPREME: 5000.0,          # 通天灵宝：独立跃升
}

# 基础攻击力（低阶法器）
BASE_ATTACK = 100
BASE_DEFENSE = 80


def calculate_artifact_stats(tier: ArtifactTier, base_stat: float) -> float:
    """
    计算法宝实际属性值（指数增长）
    
    Args:
        tier: 法宝等阶
        base_stat: 基础属性值
    
    Returns:
        实际属性值
    """
    return base_stat * TIER_MULTIPLIER[tier]


# ==================== 法力消耗体系 ====================

# 等阶对应的法力消耗百分比（相对于玩家法力上限）
TIER_MANA_COST_PERCENT = {
    ArtifactTier.LOW_MAGIC: 0.02,          # 2%
    ArtifactTier.MID_MAGIC: 0.03,          # 3%
    ArtifactTier.HIGH_MAGIC: 0.05,         # 5%
    ArtifactTier.TOP_MAGIC: 0.08,          # 8%
    ArtifactTier.LOW_ARTIFACT: 0.10,       # 10%
    ArtifactTier.MID_ARTIFACT: 0.12,       # 12%
    ArtifactTier.HIGH_ARTIFACT: 0.15,      # 15%
    ArtifactTier.TOP_ARTIFACT: 0.18,       # 18%
    ArtifactTier.LOW_TREASURE: 0.20,       # 20%
    ArtifactTier.MID_TREASURE: 0.22,       # 22%
    ArtifactTier.HIGH_TREASURE: 0.25,      # 25%
    ArtifactTier.TOP_TREASURE: 0.28,       # 28%
    ArtifactTier.LOW_SPIRIT: 0.30,         # 30%
    ArtifactTier.MID_SPIRIT: 0.35,         # 35%
    ArtifactTier.HIGH_SPIRIT: 0.40,        # 40%
    ArtifactTier.TOP_SPIRIT: 0.45,         # 45%
    ArtifactTier.SUPREME: 0.50,            # 50%（通天灵宝消耗极大）
}


def calculate_mana_cost(tier: ArtifactTier, player_mana_max: int) -> int:
    """
    计算法宝法力消耗（与法力上限挂钩）
    
    Args:
        tier: 法宝等阶
        player_mana_max: 玩家法力上限
    
    Returns:
        实际法力消耗
    """
    return int(player_mana_max * TIER_MANA_COST_PERCENT[tier])


# ==================== 功法体系 ====================

class CultivationTechnique:
    """修仙功法"""
    
    def __init__(self, name: str, element: Element, tier: str, 
                 attack_per_level: float, defense_per_level: float,
                 hp_per_level: float, special_bonus: dict):
        """
        Args:
            name: 功法名称
            element: 所属属性
            tier: 等阶（低阶/中阶/高阶/顶阶）
            attack_per_level: 每层攻击加成
            defense_per_level: 每层防御加成
            hp_per_level: 每层生命加成
            special_bonus: 特殊加成 {"暴击": 0.05, "速度": 0.03, ...}
        """
        self.name = name
        self.element = element
        self.tier = tier
        self.attack_per_level = attack_per_level
        self.defense_per_level = defense_per_level
        self.hp_per_level = hp_per_level
        self.special_bonus = special_bonus


# 功法等阶系数
TECHNIQUE_TIER_MULTIPLIER = {
    "低阶": 1.0,
    "中阶": 2.5,
    "高阶": 6.0,
    "顶阶": 15.0,
}


def calculate_technique_bonus(technique: CultivationTechnique, level: int) -> dict:
    """
    计算功法加成
    
    Args:
        technique: 功法对象
        level: 修炼层数
    
    Returns:
        属性加成字典
    """
    tier_mult = TECHNIQUE_TIER_MULTIPLIER.get(technique.tier, 1.0)
    
    bonus = {
        "attack": technique.attack_per_level * level * tier_mult,
        "defense": technique.defense_per_level * level * tier_mult,
        "hp": technique.hp_per_level * level * tier_mult,
    }
    
    # 特殊加成
    for stat, value in technique.special_bonus.items():
        bonus[stat] = value * level * tier_mult
    
    return bonus


# ==================== 通天灵宝唯一性机制 ====================

class SupremeTreasure:
    """通天灵宝（全服唯一）"""
    
    def __init__(self, name: str, effect_id: str, effect_desc: str,
                 element: Element, attack_bonus: float, defense_bonus: float,
                 special_effect: dict):
        """
        Args:
            name: 灵宝名称
            effect_id: 唯一效果ID
            effect_desc: 效果描述
            element: 五行属性
            attack_bonus: 攻击加成（百分比）
            defense_bonus: 防御加成（百分比）
            special_effect: 特殊效果 {"瞬移": True, "复活": 1, ...}
        """
        self.name = name
        self.effect_id = effect_id
        self.effect_desc = effect_desc
        self.element = element
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus
        self.special_effect = special_effect
        self.owner = None  # 当前持有者（全服唯一）
    
    def can_acquire(self) -> bool:
        """检查是否可获取（无持有者时）"""
        return self.owner is None
    
    def acquire(self, player_id: str) -> bool:
        """
        尝试获取灵宝
        
        Args:
            player_id: 玩家ID
        
        Returns:
            是否获取成功
        """
        if self.can_acquire():
            self.owner = player_id
            return True
        return False
    
    def release(self):
        """释放灵宝（持有者放弃或被击杀）"""
        self.owner = None


# 通天灵宝特殊效果类型
SUPREME_EFFECTS = {
    "TELEPORT": "瞬移",           # 瞬间移动到任意位置
    "REVIVE": "复活",             # 死亡后复活
    "IGNORE_DEFENSE": "无视防御", # 攻击无视防御
    "LIFE_STEAL": "生命汲取",     # 攻击回复生命
    "MANA_STEAL": "法力汲取",     # 攻击回复法力
    "INVINCIBLE": "无敌",         # 短暂无敌
    "TIME_STOP": "时间停滞",      # 暂停时间
    "SPACE_TEAR": "空间撕裂",     # 撕裂空间造成伤害
    "FATE_REVERSE": "命运逆转",   # 逆转因果
    "SOUL_ATTACK": "灵魂攻击",    # 直接攻击灵魂
    "ELEMENTAL_BURST": "元素爆发",# 全属性爆发
    "SUMMON_GOD": "召唤神灵",     # 召唤神灵助战
    "PURIFY": "净化",             # 净化一切负面状态
    "DEVOUR": "吞噬",             # 吞噬敌人属性
    "REBIRTH": "涅槃重生",        # 越战越强
}


# ==================== 战斗伤害计算 ====================

def calculate_damage(
    attacker_attack: float,
    attacker_element: Element,
    attacker_technique: Optional[CultivationTechnique],
    attacker_technique_level: int,
    defender_defense: float,
    defender_element: Element,
    artifact_attack_bonus: float = 0.0,
    artifact_mana_cost_percent: float = 0.0,
    player_mana_max: int = 0,
    player_mana_current: int = 0,
) -> dict:
    """
    计算最终伤害
    
    Args:
        attacker_attack: 攻击者基础攻击力
        attacker_element: 攻击者属性
        attacker_technique: 攻击者功法
        attacker_technique_level: 功法层数
        defender_defense: 防御者防御力
        defender_element: 防御者属性
        artifact_attack_bonus: 法宝攻击加成（百分比）
        artifact_mana_cost_percent: 法宝法力消耗百分比
        player_mana_max: 玩家法力上限
        player_mana_current: 玩家当前法力
    
    Returns:
        伤害计算结果
    """
    # 1. 基础攻击力
    base_damage = attacker_attack
    
    # 2. 功法加成
    if attacker_technique:
        technique_bonus = calculate_technique_bonus(attacker_technique, attacker_technique_level)
        base_damage += technique_bonus.get("attack", 0)
    
    # 3. 法宝加成
    artifact_bonus = base_damage * artifact_attack_bonus
    base_damage += artifact_bonus
    
    # 4. 五行克制
    element_multiplier = get_element_multiplier(attacker_element, defender_element)
    
    # 5. 法力充足检查（法力不足时伤害降低）
    mana_multiplier = 1.0
    if player_mana_max > 0:
        mana_cost = int(player_mana_max * artifact_mana_cost_percent)
        if player_mana_current < mana_cost:
            # 法力不足，伤害降低
            mana_multiplier = 0.5
    
    # 6. 防御计算
    final_damage = max(1, (base_damage * element_multiplier * mana_multiplier) - defender_defense)
    
    return {
        "base_damage": base_damage,
        "element_multiplier": element_multiplier,
        "mana_multiplier": mana_multiplier,
        "defense_reduction": defender_defense,
        "final_damage": int(final_damage),
        "mana_cost": int(player_mana_max * artifact_mana_cost_percent) if player_mana_max > 0 else 0,
    }


# ==================== 测试示例 ====================

if __name__ == "__main__":
    # 测试五行克制
    print("=== 五行克制测试 ===")
    print(f"金 vs 木: {get_element_multiplier(Element.METAL, Element.WOOD):.2f}x")
    print(f"木 vs 土: {get_element_multiplier(Element.WOOD, Element.EARTH):.2f}x")
    print(f"水 vs 火: {get_element_multiplier(Element.WATER, Element.FIRE):.2f}x")
    print(f"火 vs 金: {get_element_multiplier(Element.FIRE, Element.METAL):.2f}x")
    print(f"金 vs 火: {get_element_multiplier(Element.METAL, Element.FIRE):.2f}x")
    
    # 测试法宝等阶增长
    print("\n=== 法宝等阶增长测试 ===")
    for tier in [ArtifactTier.LOW_MAGIC, ArtifactTier.TOP_MAGIC, 
                 ArtifactTier.LOW_ARTIFACT, ArtifactTier.TOP_ARTIFACT,
                 ArtifactTier.SUPREME]:
        attack = calculate_artifact_stats(tier, BASE_ATTACK)
        mana_cost_pct = TIER_MANA_COST_PERCENT[tier]
        print(f"{tier.value}: 攻击={attack:.0f}, 法力消耗={mana_cost_pct*100:.0f}%")
    
    # 测试战斗伤害
    print("\n=== 战斗伤害测试 ===")
    result = calculate_damage(
        attacker_attack=1000,
        attacker_element=Element.METAL,
        attacker_technique=None,
        attacker_technique_level=0,
        defender_defense=500,
        defender_element=Element.WOOD,  # 被金克制
        artifact_attack_bonus=0.5,
        artifact_mana_cost_percent=0.10,
        player_mana_max=10000,
        player_mana_current=10000,
    )
    print(f"金系攻击者 vs 木系防御者:")
    print(f"  基础伤害: {result['base_damage']:.0f}")
    print(f"  五行倍率: {result['element_multiplier']:.2f}x")
    print(f"  最终伤害: {result['final_damage']}")
    print(f"  法力消耗: {result['mana_cost']}")
