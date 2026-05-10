LIFE_SKILL_RECIPES = {
    "alchemy": [
        {
            "id": "qi_recovery_pill_1",
            "name": "回气丹",
            "skill_type": "alchemy",
            "required_realm": "炼气",
            "required_items": {
                "spirit_grass": 2,
                "clear_dew": 1,
            },
            "mana_cost": 10,
            "output_item_id": "qi_recovery_pill",
            "output_count": 1,
            "success_rate": 1.0,
            "required_sect": None,
            "required_contribution": 0,
            "description": "炼制回气丹，消耗少量法力恢复。",
        },
        {
            "id": "healing_pill_1",
            "name": "疗伤丹",
            "skill_type": "alchemy",
            "required_realm": "炼气",
            "required_items": {
                "healing_herb": 2,
            },
            "mana_cost": 8,
            "output_item_id": "healing_pill",
            "output_count": 1,
            "success_rate": 1.0,
            "required_sect": None,
            "required_contribution": 0,
            "description": "炼制疗伤丹，恢复少量气血。",
        },
        {
            "id": "foundation_pill_1",
            "name": "筑基丹",
            "skill_type": "alchemy",
            "required_realm": "炼气",
            "required_items": {
                "spirit_grass": 5,
                "beast_core": 1,
                "mid_spirit_stone": 1,
            },
            "mana_cost": 25,
            "output_item_id": "foundation_pill",
            "output_count": 1,
            "success_rate": 0.8,
            "required_sect": None,
            "required_contribution": 0,
            "description": "炼制筑基丹，冲击筑基期的关键丹药。",
        },
        {
            "id": "qi_powder_1",
            "name": "聚气散",
            "skill_type": "alchemy",
            "required_realm": "炼气",
            "required_items": {
                "spirit_grass": 3,
            },
            "mana_cost": 12,
            "output_item_id": "qi_powder",
            "output_count": 1,
            "success_rate": 1.0,
            "required_sect": None,
            "required_contribution": 0,
            "description": "炼制聚气散，辅助炼气期修士吸纳灵气。",
        },
    ],
    "talisman": [
        {
            "id": "scout_talisman_1",
            "name": "探查符",
            "skill_type": "talisman",
            "required_realm": "炼气",
            "required_items": {
                "spirit_paper": 2,
                "spirit_ink": 1,
            },
            "mana_cost": 8,
            "output_item_id": "scout_talisman",
            "output_count": 1,
            "success_rate": 1.0,
            "required_sect": None,
            "required_contribution": 0,
            "description": "绘制探查符，提高秘境触发概率。",
        },
        {
            "id": "protect_talisman_1",
            "name": "护身符",
            "skill_type": "talisman",
            "required_realm": "炼气",
            "required_items": {
                "spirit_paper": 2,
                "spirit_grass": 1,
            },
            "mana_cost": 8,
            "output_item_id": "protect_talisman",
            "output_count": 1,
            "success_rate": 1.0,
            "required_sect": None,
            "required_contribution": 0,
            "description": "绘制护身符，降低探索负面事件概率。",
        },
        {
            "id": "speed_talisman_1",
            "name": "速行符",
            "skill_type": "talisman",
            "required_realm": "炼气",
            "required_items": {
                "spirit_paper": 3,
            },
            "mana_cost": 6,
            "output_item_id": "speed_talisman",
            "output_count": 1,
            "success_rate": 1.0,
            "required_sect": None,
            "required_contribution": 0,
            "description": "绘制速行符，降低探索法力消耗。",
        },
    ],
    "crafting": [
        {
            "id": "low_sword_1",
            "name": "下品法剑",
            "skill_type": "crafting",
            "required_realm": "炼气",
            "required_items": {
                "black_iron_shard": 3,
                "low_material": 2,
            },
            "mana_cost": 15,
            "output_item_id": "low_artifact",
            "output_count": 1,
            "success_rate": 0.75,
            "required_sect": None,
            "required_contribution": 0,
            "description": "炼制下品法剑，提升战斗能力。",
        },
        {
            "id": "spirit_gather_artifact_1",
            "name": "聚灵法器",
            "skill_type": "crafting",
            "required_realm": "炼气",
            "required_items": {
                "mid_material": 2,
                "beast_core": 1,
            },
            "mana_cost": 20,
            "output_item_id": "spirit_gather_artifact",
            "output_count": 1,
            "success_rate": 0.7,
            "required_sect": None,
            "required_contribution": 0,
            "description": "炼制聚灵法器，提升修炼效率。",
        },
        {
            "id": "explore_puppet_1",
            "name": "探索傀儡",
            "skill_type": "crafting",
            "required_realm": "炼气",
            "required_items": {
                "low_material": 4,
                "beast_core": 2,
            },
            "mana_cost": 25,
            "output_item_id": "explore_puppet",
            "output_count": 1,
            "success_rate": 0.6,
            "required_sect": None,
            "required_contribution": 0,
            "description": "炼制探索傀儡，提高掉落概率。",
        },
    ],
    "formation": [
        {
            "id": "spirit_gather_formation_1",
            "name": "聚灵阵",
            "skill_type": "formation",
            "required_realm": "炼气",
            "required_items": {
                "formation_flag": 3,
                "spirit_stone_chip": 5,
            },
            "mana_cost": 20,
            "output_item_id": "spirit_gather_formation",
            "output_count": 1,
            "success_rate": 1.0,
            "required_sect": None,
            "required_contribution": 0,
            "description": "布置聚灵阵，提升修炼效率。",
        },
        {
            "id": "protect_formation_1",
            "name": "防护阵",
            "skill_type": "formation",
            "required_realm": "炼气",
            "required_items": {
                "formation_flag": 2,
                "spirit_grass": 2,
            },
            "mana_cost": 15,
            "output_item_id": "protect_formation",
            "output_count": 1,
            "success_rate": 1.0,
            "required_sect": None,
            "required_contribution": 0,
            "description": "布置防护阵，降低探索风险。",
        },
        {
            "id": "attract_formation_1",
            "name": "引灵阵",
            "skill_type": "formation",
            "required_realm": "炼气",
            "required_items": {
                "formation_flag": 4,
                "beast_core": 1,
            },
            "mana_cost": 25,
            "output_item_id": "attract_formation",
            "output_count": 1,
            "success_rate": 1.0,
            "required_sect": None,
            "required_contribution": 0,
            "description": "布置引灵阵，增加资源获取概率。",
        },
    ],
}


LIFE_SKILL_MANA_COSTS = {
    "alchemy": 10,
    "talisman": 8,
    "crafting": 15,
    "formation": 20,
}


def get_recipes_by_type(skill_type: str) -> list[dict]:
    return LIFE_SKILL_RECIPES.get(skill_type, [])


def get_recipe_by_id(recipe_id: str) -> dict | None:
    for recipes in LIFE_SKILL_RECIPES.values():
        for recipe in recipes:
            if recipe["id"] == recipe_id:
                return recipe
    return None


def get_all_recipes() -> list[dict]:
    recipes = []
    for recipe_list in LIFE_SKILL_RECIPES.values():
        recipes.extend(recipe_list)
    return recipes
