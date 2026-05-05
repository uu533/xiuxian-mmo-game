LUCKY_EVENT_CONFIG = {
    "base_rate": 0.01,
    "max_rate": 0.05,
    "luck_factor": 0.0003,
}

LUCKY_EVENTS = [
    {
        "code": "lucky_breakthrough",
        "name": "顿悟破境",
        "type": "lucky_breakthrough",
        "weight": 1,
        "description": "你忽然明悟关窍，当前小境界的瓶颈松动。",
    },
    {
        "code": "rare_item",
        "name": "天降灵物",
        "type": "rare_item",
        "weight": 3,
        "description": "你在草木间发现一件少见灵物。",
    },
    {
        "code": "master_teach",
        "name": "高人指点",
        "type": "master_teach",
        "weight": 2,
        "description": "一位路过前辈随手点拨了你的功法。",
    },
    {
        "code": "hidden_cave",
        "name": "隐秘洞府",
        "type": "hidden_cave",
        "weight": 2,
        "description": "你发现一处被藤蔓遮掩的洞府。",
    },
]
