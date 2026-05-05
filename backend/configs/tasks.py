TASKS = [
    {
        "id": "task_001",
        "name": "初入修行",
        "type": "train",
        "target": 5,
        "reward": {"spirit_stones": 50},
        "description": "完成 5 次修炼，熟悉吐纳节奏。",
    },
    {
        "id": "task_002",
        "name": "山野初探",
        "type": "explore",
        "target": 3,
        "reward": {"spirit_stones": 80, "items": [{"code": "mana_pill", "quantity": 1}]},
        "description": "完成 3 次探索，获得第一批修行资源。",
    },
    {
        "id": "task_003",
        "name": "功法入门",
        "type": "learn_method",
        "target": 1,
        "reward": {"spirit_stones": 120, "items": [{"code": "foundation_pill", "quantity": 1}]},
        "description": "学习任意一门功法，为筑基做准备。",
    },
    {
        "id": "task_004",
        "name": "法宝护身",
        "type": "equip_artifact",
        "target": 1,
        "reward": {"spirit_stones": 120, "items": [{"code": "low_material", "quantity": 2}]},
        "description": "装备任意一件法宝，提升斗法安全感。",
    },
    {
        "id": "task_005",
        "name": "筑基问道",
        "type": "breakthrough_realm",
        "target": 1,
        "target_realm_stage": "筑基",
        "reward": {"spirit_stones": 300, "items": [{"code": "mid_material", "quantity": 2}]},
        "description": "突破至筑基期，正式踏入修仙门槛。",
    },
]

TASK_BY_ID = {task["id"]: task for task in TASKS}
