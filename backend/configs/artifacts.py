ARTIFACT_UPGRADE = {
    "base_spirit_stone_cost": 25,
    "cost_growth": 18,
    "max_level": 10,
    "success_rate_by_rarity": {
        "白": 0.88,
        "绿": 0.78,
        "蓝": 0.66,
        "紫": 0.52,
        "金": 0.38,
    },
}

ARTIFACT_EFFECTS_BY_CODE = {
    "low_artifact": {
        "attack_per_level": 8,
        "defense_per_level": 5,
        "explore_reward_bonus_per_level": 0.02,
        "battle_power_per_level": 3,
        "max_mana_per_level": 4,
    },
    "mid_artifact": {
        "attack_per_level": 18,
        "defense_per_level": 12,
        "explore_reward_bonus_per_level": 0.035,
        "battle_power_per_level": 8,
        "max_mana_per_level": 10,
    },
    "high_artifact": {
        "attack_per_level": 40,
        "defense_per_level": 25,
        "explore_reward_bonus_per_level": 0.05,
        "battle_power_per_level": 18,
        "max_mana_per_level": 20,
    },
    "crafted_low_sword": {
        "attack_per_level": 6,
        "defense_per_level": 3,
        "explore_reward_bonus_per_level": 0.01,
        "battle_power_per_level": 2,
        "max_mana_per_level": 2,
    },
    "gathering_artifact": {
        "attack_per_level": 3,
        "defense_per_level": 4,
        "cultivation_speed_per_level": 0.02,
        "explore_reward_bonus_per_level": 0.015,
        "battle_power_per_level": 1,
        "max_mana_per_level": 3,
    },
    "explore_puppet": {
        "attack_per_level": 2,
        "defense_per_level": 3,
        "explore_reward_bonus_per_level": 0.015,
        "battle_power_per_level": 1,
        "max_mana_per_level": 2,
    },
    "qingmu_pendant": {
        "attack_per_level": 4,
        "defense_per_level": 3,
        "explore_reward_bonus_per_level": 0.015,
        "battle_power_per_level": 2,
        "max_mana_per_level": 5,
    },
    "juqi_jade": {
        "attack_per_level": 2,
        "defense_per_level": 2,
        "battle_power_per_level": 1,
        "max_mana_per_level": 6,
    },
    "hushen_bell": {
        "attack_per_level": 3,
        "defense_per_level": 3,
        "battle_power_per_level": 2,
        "max_mana_per_level": 3,
    },
}

RARITY_WEIGHTS = [
    {"rarity": "白", "weight": 52},
    {"rarity": "绿", "weight": 28},
    {"rarity": "蓝", "weight": 14},
    {"rarity": "紫", "weight": 5},
    {"rarity": "金", "weight": 1},
]
