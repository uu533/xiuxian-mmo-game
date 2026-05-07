from dataclasses import dataclass


@dataclass(frozen=True)
class RealmConfig:
    name: str
    stage: str
    cultivation_cap: int
    breakthrough_rate: float


REALMS: list[RealmConfig] = [
    RealmConfig("炼气一层", "炼气", 80, 0.88),
    RealmConfig("炼气二层", "炼气", 120, 0.86),
    RealmConfig("炼气三层", "炼气", 170, 0.84),
    RealmConfig("炼气四层", "炼气", 240, 0.82),
    RealmConfig("炼气五层", "炼气", 330, 0.80),
    RealmConfig("炼气六层", "炼气", 450, 0.78),
    RealmConfig("炼气七层", "炼气", 620, 0.76),
    RealmConfig("炼气八层", "炼气", 820, 0.74),
    RealmConfig("炼气九层", "炼气", 1080, 0.72),
    RealmConfig("炼气十层", "炼气", 1420, 0.68),
    RealmConfig("炼气十一层", "炼气", 1880, 0.62),
    RealmConfig("炼气十二层", "炼气", 2500, 0.46),
    RealmConfig("筑基初期", "筑基", 4200, 0.56),
    RealmConfig("筑基中期", "筑基", 6800, 0.48),
    RealmConfig("筑基后期", "筑基", 10500, 0.34),
    RealmConfig("结丹初期", "结丹", 17000, 0.32),
    RealmConfig("结丹中期", "结丹", 28000, 0.24),
    RealmConfig("结丹后期", "结丹", 46000, 0.12),
    RealmConfig("元婴初期", "元婴", 92000, 0.14),
    RealmConfig("元婴中期", "元婴", 165000, 0.10),
    RealmConfig("元婴后期", "元婴", 280000, 0.07),
    RealmConfig("化神初期", "化神", 520000, 0.08),
    RealmConfig("化神中期", "化神", 900000, 0.05),
    RealmConfig("化神后期", "化神", 1_500_000, 0.03),
]

REALM_NAMES = [realm.name for realm in REALMS]
REALM_BY_NAME = {realm.name: realm for realm in REALMS}
STARTING_REALM = REALMS[0]

LEGACY_REALM_MAP = {
    "炼气": "炼气一层",
    "筑基": "筑基初期",
    "金丹": "结丹初期",
    "结丹": "结丹初期",
    "元婴": "元婴初期",
    "化神": "化神初期",
}

TITLE_UNLOCKS = {
    "炼气": ["师兄", "师姐"],
    "筑基": ["师兄", "师姐", "师叔", "师伯", "前辈"],
    "结丹": ["师兄", "师姐", "师叔", "师伯", "前辈", "道人", "真人", "老祖", "真君", "尊者"],
    "元婴": ["师兄", "师姐", "师叔", "师伯", "前辈", "道人", "真人", "老祖", "真君", "尊者", "大修士", "元君", "天君", "法王", "上人"],
    "化神": ["师兄", "师姐", "师叔", "师伯", "前辈", "道人", "真人", "老祖", "真君", "尊者", "大修士", "元君", "天君", "法王", "上人", "道尊", "神君", "圣君", "尊上"],
}
