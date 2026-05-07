import random
from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def weighted_choice(items: Iterable[T], weight_getter) -> T:
    values = list(items)
    total = sum(max(0, weight_getter(item)) for item in values)
    if total <= 0:
        return random.choice(values)
    pick = random.uniform(0, total)
    current = 0.0
    for item in values:
        current += max(0, weight_getter(item))
        if pick <= current:
            return item
    return values[-1]
