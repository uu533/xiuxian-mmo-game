# Goal Chain Configuration
# MVP - only read-only goal generation, no player state modification

# Maximum goals per request
MAX_TOTAL_GOALS = 3
MAX_SHORT_TERM = 2
MAX_LONG_TERM = 1

# Priority thresholds
BREAKTHROUGH_APPROACH_THRESHOLD = 0.70  # 70% of cultivation cap
SECT_PROMOTION_APPROACH_THRESHOLD = 0.70  # 70% of promotion contribution requirement

# Priority values (higher = more important)
PRIORITY_SECT_TASK = 900
PRIORITY_MATERIAL_EXPLORE = 800
PRIORITY_LIFE_SKILL = 750
PRIORITY_MANA_ACTION = 600
PRIORITY_BREAKTHROUGH = 850
PRIORITY_SECT_PROMOTION = 700
PRIORITY_LONG_BREAKTHROUGH = 500
PRIORITY_LONG_SECT_PROMOTION = 400