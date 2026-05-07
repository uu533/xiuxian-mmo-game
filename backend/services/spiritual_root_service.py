import secrets
from dataclasses import dataclass

FIVE_ELEMENTS = ["金", "木", "水", "火", "土"]
VARIANT_ELEMENTS = ["雷", "冰", "光", "暗"]


@dataclass(frozen=True)
class SpiritualRootProfile:
    name: str
    rate: float
    base_luck: int
    description: str


def build_spiritual_root(elements: list[str], is_variant: bool = False) -> SpiritualRootProfile:
    if is_variant:
        element = elements[0]
        return SpiritualRootProfile(
            name=f"{element}属性异灵根",
            rate=1.05,
            base_luck=58,
            description="异灵根属性特殊，修炼速度约等同三灵根，但部分机缘和斗法潜力更独特。",
        )

    count = len(elements)
    label = "".join(elements)
    if count == 1:
        return SpiritualRootProfile(
            name=f"{label}属性天灵根",
            rate=1.45,
            base_luck=44,
            description="单一五行属性，灵气纯净，修炼速度最快。",
        )
    if count == 2:
        return SpiritualRootProfile(
            name=f"{label}双灵根",
            rate=1.25,
            base_luck=50,
            description="两种五行属性并存，资质上佳，修炼速度仅次于天灵根。",
        )
    if count == 3:
        return SpiritualRootProfile(
            name=f"{label}三灵根",
            rate=1.05,
            base_luck=56,
            description="三种五行属性并存，资质中正，修炼速度平稳。",
        )
    if count == 4:
        return SpiritualRootProfile(
            name=f"{label}伪灵根",
            rate=0.88,
            base_luck=63,
            description="四种五行属性牵扯，灵气驳杂，修炼速度偏慢。",
        )
    return SpiritualRootProfile(
        name="金木水火土杂灵根",
        rate=0.72,
        base_luck=72,
        description="五行俱全但过于驳杂，修炼速度最慢，更依赖资源与机缘。",
    )


SPIRITUAL_ROOT_PROFILES: list[SpiritualRootProfile] = [
    *[build_spiritual_root([element]) for element in FIVE_ELEMENTS],
    *[build_spiritual_root(list(elements)) for elements in [("金", "木"), ("金", "水"), ("木", "火"), ("水", "土"), ("火", "土")]],
    *[build_spiritual_root(list(elements)) for elements in [("金", "木", "水"), ("木", "火", "土"), ("金", "水", "火"), ("水", "火", "土")]],
    build_spiritual_root(["金", "木", "水", "火"]),
    build_spiritual_root(["金", "木", "火", "土"]),
    build_spiritual_root(FIVE_ELEMENTS),
    *[build_spiritual_root([element], is_variant=True) for element in VARIANT_ELEMENTS],
]

LEGACY_ROOT_RATES = {
    "天灵根": 1.45,
    "双灵根": 1.25,
    "三灵根": 1.05,
    "四灵根": 0.88,
    "五行杂灵根": 0.72,
}


def random_spiritual_root() -> SpiritualRootProfile:
    return secrets.choice(SPIRITUAL_ROOT_PROFILES)


def root_rate(root: str) -> float:
    for profile in SPIRITUAL_ROOT_PROFILES:
        if profile.name == root:
            return profile.rate
    for legacy_name, rate in LEGACY_ROOT_RATES.items():
        if root == legacy_name:
            return rate
    if "天灵根" in root:
        return 1.45
    if "双灵根" in root:
        return 1.25
    if "三灵根" in root or "异灵根" in root:
        return 1.05
    if "伪灵根" in root:
        return 0.88
    if "杂灵根" in root:
        return 0.72
    return 1.0
