METHOD_LEVEL_EXP = {
    1: 60,
    2: 120,
    3: 240,
    4: 420,
    5: 680,
    6: 1040,
    7: 1500,
    8: 2100,
    9: 3000,
}

METHOD_PRACTICE = {
    "mana_cost": 10,
    "exp_gain": [35, 55],
    "max_level": 10,
}

METHOD_EFFECTS_BY_CODE = {
    "low_method": {
        "cultivation_speed_per_level": 0.04,
        "max_mana_per_level": 12,
        "breakthrough_rate_per_level": 0.01,
    },
    "mid_method": {
        "cultivation_speed_per_level": 0.06,
        "max_mana_per_level": 24,
        "breakthrough_rate_per_level": 0.014,
    },
    "high_method": {
        "cultivation_speed_per_level": 0.08,
        "max_mana_per_level": 40,
        "breakthrough_rate_per_level": 0.018,
    },
}
