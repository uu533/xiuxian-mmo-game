from dataclasses import dataclass

from backend.models import Character


@dataclass(frozen=True)
class RealmStep:
    name: str
    cultivation_cap: int
    breakthrough_rate: float
    lifespan_bonus: int = 0
    hp_bonus: int = 0
    mana_bonus: int = 0
    attack_bonus: int = 0
    defense_bonus: int = 0


REALM_STEPS: list[RealmStep] = [
    RealmStep("炼气一层", 80, 0.88, mana_bonus=2),
    RealmStep("炼气二层", 120, 0.86, mana_bonus=2),
    RealmStep("炼气三层", 170, 0.84, hp_bonus=4, mana_bonus=3),
    RealmStep("炼气四层", 240, 0.82, mana_bonus=3),
    RealmStep("炼气五层", 330, 0.80, attack_bonus=1),
    RealmStep("炼气六层", 450, 0.78, hp_bonus=6, mana_bonus=4),
    RealmStep("炼气七层", 620, 0.76, defense_bonus=1),
    RealmStep("炼气八层", 820, 0.74, mana_bonus=5),
    RealmStep("炼气九层", 1080, 0.72, hp_bonus=8, attack_bonus=2),
    RealmStep("炼气十层", 1420, 0.68, mana_bonus=6),
    RealmStep("炼气十一层", 1880, 0.62, defense_bonus=2),
    RealmStep("炼气十二层", 2500, 0.46, hp_bonus=12, mana_bonus=8, attack_bonus=2),
    RealmStep("筑基初期", 4200, 0.56, lifespan_bonus=70, hp_bonus=36, mana_bonus=28, attack_bonus=8, defense_bonus=5),
    RealmStep("筑基中期", 6800, 0.48, hp_bonus=28, mana_bonus=24, attack_bonus=6, defense_bonus=4),
    RealmStep("筑基后期", 10500, 0.34, hp_bonus=34, mana_bonus=30, attack_bonus=8, defense_bonus=5),
    RealmStep("结丹初期", 17000, 0.32, lifespan_bonus=130, hp_bonus=70, mana_bonus=65, attack_bonus=18, defense_bonus=12),
    RealmStep("结丹中期", 28000, 0.24, hp_bonus=55, mana_bonus=52, attack_bonus=14, defense_bonus=10),
    RealmStep("结丹后期", 46000, 0.12, hp_bonus=68, mana_bonus=64, attack_bonus=16, defense_bonus=12),
    RealmStep("元婴初期", 92000, 0.14, lifespan_bonus=260, hp_bonus=150, mana_bonus=150, attack_bonus=38, defense_bonus=28),
    RealmStep("元婴中期", 165000, 0.10, hp_bonus=115, mana_bonus=130, attack_bonus=30, defense_bonus=24),
    RealmStep("元婴后期", 280000, 0.07, hp_bonus=140, mana_bonus=160, attack_bonus=36, defense_bonus=30),
    RealmStep("化神初期", 520000, 0.08, lifespan_bonus=500, hp_bonus=260, mana_bonus=280, attack_bonus=68, defense_bonus=54),
    RealmStep("化神中期", 900000, 0.05, hp_bonus=220, mana_bonus=260, attack_bonus=56, defense_bonus=46),
    RealmStep("化神后期", 1500000, 0.03, hp_bonus=260, mana_bonus=320, attack_bonus=72, defense_bonus=60),
]

REALMS = [step.name for step in REALM_STEPS]
STARTING_REALM = REALMS[0]
STARTING_CULTIVATION_CAP = REALM_STEPS[0].cultivation_cap
TITLE_UNLOCKS = {
    0: ["师兄", "师姐"],
    1: ["师兄", "师姐", "师叔", "师伯", "前辈"],
    2: ["师兄", "师姐", "师叔", "师伯", "前辈", "道人", "真人", "老祖", "真君", "尊者"],
    3: ["师兄", "师姐", "师叔", "师伯", "前辈", "道人", "真人", "老祖", "真君", "尊者", "大修士", "元君", "天君", "法王", "上人"],
    4: ["师兄", "师姐", "师叔", "师伯", "前辈", "道人", "真人", "老祖", "真君", "尊者", "大修士", "元君", "天君", "法王", "上人", "道尊", "神君", "圣君", "尊上"],
}

LEGACY_REALM_MAP = {
    "炼气": "炼气一层",
    "筑基": "筑基初期",
    "金丹": "结丹初期",
    "结丹": "结丹初期",
    "元婴": "元婴初期",
    "化神": "化神初期",
}


def normalize_realm(character: Character) -> None:
    if character.realm in LEGACY_REALM_MAP:
        character.realm = LEGACY_REALM_MAP[character.realm]
    if character.realm not in REALMS:
        character.realm = STARTING_REALM
    current = current_step(character)
    if character.cultivation_cap < current.cultivation_cap:
        character.cultivation_cap = current.cultivation_cap


def current_index(character: Character) -> int:
    normalize_realm(character)
    return REALMS.index(character.realm)


def current_step(character: Character) -> RealmStep:
    return REALM_STEPS[REALMS.index(character.realm)]


def next_step(character: Character) -> RealmStep | None:
    index = current_index(character)
    if index >= len(REALM_STEPS) - 1:
        return None
    return REALM_STEPS[index + 1]


def realm_tier(name: str) -> int:
    if name.startswith("炼气"):
        return 0
    if name.startswith("筑基"):
        return 1
    if name.startswith("结丹"):
        return 2
    if name.startswith("元婴"):
        return 3
    return 4


def is_major_breakthrough(from_name: str, to_name: str) -> bool:
    return realm_tier(to_name) > realm_tier(from_name)


def unlocked_titles(realm_name: str) -> list[str]:
    return TITLE_UNLOCKS[realm_tier(realm_name)]


def normalize_title(character: Character) -> None:
    normalize_realm(character)
    available = unlocked_titles(character.realm)
    if not character.title or character.title not in available:
        character.title = available[0]
