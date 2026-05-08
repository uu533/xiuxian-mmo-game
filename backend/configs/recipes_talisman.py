from backend.configs.realms import REALM_NAMES


TALISMAN_RECIPES = [
    {
        "id": "talisman_scout",
        "name": "Scout Talisman",
        "skill_type": "talisman",
        "required_items": [
            {"code": "low_material", "quantity": 1},
            {"code": "low_spirit_stone", "quantity": 4},
        ],
        "mana_cost": 16,
        "output_item_id": "scout_talisman",
        "output_count": 1,
        "required_realm": REALM_NAMES[0],
        "success_rate": 1.0,
    },
    {
        "id": "talisman_guard",
        "name": "Guard Talisman",
        "skill_type": "talisman",
        "required_items": [
            {"code": "calm_talisman", "quantity": 1},
            {"code": "low_material", "quantity": 1},
        ],
        "mana_cost": 16,
        "output_item_id": "guard_talisman",
        "output_count": 1,
        "required_realm": REALM_NAMES[0],
        "success_rate": 1.0,
    },
    {
        "id": "talisman_swift",
        "name": "Swift Talisman",
        "skill_type": "talisman",
        "required_items": [
            {"code": "low_material", "quantity": 2},
            {"code": "low_spirit_stone", "quantity": 6},
        ],
        "mana_cost": 22,
        "output_item_id": "swift_talisman",
        "output_count": 1,
        "required_realm": REALM_NAMES[3],
        "success_rate": 1.0,
        "unlock_item": "swift_talisman_formula",
    },
]
