from backend.configs.realms import REALM_NAMES


CRAFTING_RECIPES = [
    {
        "id": "craft_low_sword",
        "name": "Low Grade Sword",
        "skill_type": "crafting",
        "required_items": [
            {"code": "low_material", "quantity": 6},
            {"code": "low_spirit_stone", "quantity": 16},
        ],
        "mana_cost": 28,
        "output_item_id": "crafted_low_sword",
        "output_count": 1,
        "required_realm": REALM_NAMES[0],
        "success_rate": 1.0,
    },
    {
        "id": "craft_gathering_artifact",
        "name": "Gathering Artifact",
        "skill_type": "crafting",
        "required_items": [
            {"code": "low_material", "quantity": 6},
            {"code": "low_spirit_stone", "quantity": 12},
        ],
        "mana_cost": 30,
        "output_item_id": "gathering_artifact",
        "output_count": 1,
        "required_realm": REALM_NAMES[2],
        "success_rate": 1.0,
    },
    {
        "id": "craft_explore_puppet",
        "name": "Explore Puppet",
        "skill_type": "crafting",
        "required_items": [
            {"code": "low_material", "quantity": 8},
            {"code": "beast_core", "quantity": 1},
        ],
        "mana_cost": 38,
        "output_item_id": "explore_puppet",
        "output_count": 1,
        "required_realm": REALM_NAMES[5],
        "success_rate": 1.0,
        "unlock_item": "explore_puppet_formula",
    },
]
