from backend.configs.realms import REALM_NAMES


FORMATION_RECIPES = [
    {
        "id": "formation_gather_spirit",
        "name": "聚灵阵",
        "skill_type": "formation",
        "required_items": [
            {"code": "low_spirit_stone", "quantity": 10},
            {"code": "low_material", "quantity": 2},
        ],
        "mana_cost": 32,
        "output_effect_id": "formation_gather_spirit",
        "required_realm": REALM_NAMES[2],
        "success_rate": 1.0,
    },
    {
        "id": "formation_guard",
        "name": "护身阵",
        "skill_type": "formation",
        "required_items": [
            {"code": "low_spirit_stone", "quantity": 14},
            {"code": "low_material", "quantity": 2},
        ],
        "mana_cost": 30,
        "output_effect_id": "formation_guard",
        "required_realm": REALM_NAMES[2],
        "success_rate": 1.0,
    },
    {
        "id": "formation_draw_spirit",
        "name": "引灵阵",
        "skill_type": "formation",
        "required_items": [
            {"code": "low_spirit_stone", "quantity": 18},
            {"code": "low_material", "quantity": 3},
        ],
        "mana_cost": 36,
        "output_effect_id": "formation_draw_spirit",
        "required_realm": REALM_NAMES[4],
        "success_rate": 1.0,
    },
]
