ACTION_CONFIGS = {
    "train": {
        "mana_cost": 12,
        "log_type": "train",
    },
    "explore": {
        "mana_cost": 18,
        "log_type": "explore",
    },
    "breakthrough": {
        "mana_cost": 35,
        "log_type": "breakthrough",
    },
    "recover_mana_meditate": {
        "mana_cost": 0,
        "recover_mana": 30,
        "log_type": "recover",
    },
    "recover_mana_stone": {
        "mana_cost": 0,
        "spirit_stone_cost": 10,
        "recover_mana": 60,
        "log_type": "recover",
    },
    "use_item": {
        "mana_cost": 0,
        "log_type": "inventory",
    },
}

MANA_HELP_TEXT = "法力不足，可通过打坐恢复法力、吸收灵石恢复法力，或服用丹药恢复法力。"
