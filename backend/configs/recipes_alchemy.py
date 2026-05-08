from backend.configs.realms import REALM_NAMES


ALCHEMY_RECIPES = [
    {
        "id": "alchemy_mana_pill",
        "name": "Huiqi Dan",
        "skill_type": "alchemy",
        "required_items": [
            {"code": "low_material", "quantity": 2},
            {"code": "low_spirit_stone", "quantity": 8},
        ],
        "mana_cost": 22,
        "output_item_id": "mana_pill",
        "output_count": 1,
        "required_realm": REALM_NAMES[0],
        "success_rate": 1.0,
    },
    {
        "id": "alchemy_qi_powder",
        "name": "Juqi San",
        "skill_type": "alchemy",
        "required_items": [
            {"code": "healing_pill", "quantity": 1},
            {"code": "low_material", "quantity": 1},
            {"code": "low_spirit_stone", "quantity": 4},
        ],
        "mana_cost": 18,
        "output_item_id": "qi_powder",
        "output_count": 1,
        "required_realm": REALM_NAMES[0],
        "success_rate": 1.0,
    },
    {
        "id": "alchemy_foundation_pill",
        "name": "Foundation Pill",
        "skill_type": "alchemy",
        "required_items": [
            {"code": "healing_pill", "quantity": 4},
            {"code": "beast_core", "quantity": 1},
            {"code": "low_material", "quantity": 6},
        ],
        "mana_cost": 45,
        "output_item_id": "foundation_pill",
        "output_count": 1,
        "required_realm": REALM_NAMES[7],
        "success_rate": 1.0,
        "unlock_item": "foundation_pill_formula",
    },
]
