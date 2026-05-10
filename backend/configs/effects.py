ACTIVE_EFFECT_LIMITS = {
    "max_effects_per_type": 1,
    "refresh_remaining_uses": True,
}

ITEM_ACTIVE_EFFECTS = {
    "scout_talisman": {
        "effect_type": "explore_luck_bonus",
        "remaining_uses": 1,
        "value": 0.06,
    },
    "guard_talisman": {
        "effect_type": "explore_damage_reduction",
        "remaining_uses": 1,
        "value": 0.45,
    },
    "swift_talisman": {
        "effect_type": "explore_mana_discount",
        "remaining_uses": 1,
        "value": 6,
    },
}

FORMATION_EFFECTS = {
    "formation_gather_spirit": {
        "effect_type": "train_cultivation_bonus",
        "remaining_uses": 3,
        "value": 0.12,
    },
    "formation_guard": {
        "effect_type": "explore_damage_reduction",
        "remaining_uses": 3,
        "value": 0.35,
    },
    "formation_draw_spirit": {
        "effect_type": "explore_reward_bonus",
        "remaining_uses": 3,
        "value": 0.08,
    },
}
