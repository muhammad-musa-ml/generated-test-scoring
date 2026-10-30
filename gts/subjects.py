"""Ten small subjects: a reference function, its whole input domain and the thresholds its spec states.

The domain is small enough to run every input, so "can this mutant be told apart from the original
at all" has an exact answer instead of an estimate. A spec threshold is a number the requirement text
names for one parameter ("free shipping up to 5 kg"); the boundary generator reads only these.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, eq=False)
class Subject:
    name: str
    source: str  # defines f(...), the reference behaviour
    params: tuple  # ((parameter name, tuple of every allowed value), ...)
    thresholds: dict  # parameter name -> numbers the spec states for it (may be empty)


def _span(lo: int, hi: int, step: int = 1) -> tuple:
    return tuple(range(lo, hi + 1, step))


BOOL = (False, True)

SUBJECTS = (
    Subject(
        "clamp5",
        "def f(x):\n"
        "    if x < -5:\n"
        "        return -5\n"
        "    if x > 5:\n"
        "        return 5\n"
        "    return x\n",
        (("x", _span(-20, 20)),),
        {"x": (-5, 5)},
    ),
    Subject(
        "leap_year",
        "def f(y):\n"
        "    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)\n",
        (("y", _span(1, 800)),),
        {"y": (4, 100, 400)},
    ),
    Subject(
        "grade",
        "def f(score):\n"
        "    if score >= 90:\n"
        "        return 'A'\n"
        "    if score >= 80:\n"
        "        return 'B'\n"
        "    if score >= 70:\n"
        "        return 'C'\n"
        "    if score >= 60:\n"
        "        return 'D'\n"
        "    return 'F'\n",
        (("score", _span(0, 100)),),
        {"score": (60, 70, 80, 90)},
    ),
    Subject(
        "shipping_fee",
        "def f(weight, express):\n"
        "    if weight <= 5:\n"
        "        fee = 5\n"
        "    elif weight <= 20:\n"
        "        fee = 12\n"
        "    else:\n"
        "        fee = 12 + (weight - 20) * 2\n"
        "    if express:\n"
        "        fee = fee + 10\n"
        "    return fee\n",
        (("weight", _span(0, 60)), ("express", BOOL)),
        {"weight": (5, 20)},
    ),
    Subject(
        "discount",
        "def f(qty, member):\n"
        "    rate = 0\n"
        "    if qty >= 10:\n"
        "        rate = 5\n"
        "    if qty >= 50:\n"
        "        rate = 15\n"
        "    if member:\n"
        "        rate = rate + 5\n"
        "    return rate\n",
        (("qty", _span(0, 60)), ("member", BOOL)),
        {"qty": (10, 50)},
    ),
    Subject(
        "late_fee",
        "def f(days, balance):\n"
        "    if days <= 5:\n"
        "        return 0\n"
        "    fee = (days - 5) * 2\n"
        "    if fee > balance // 10:\n"
        "        fee = balance // 10\n"
        "    return fee\n",
        (("days", _span(0, 40)), ("balance", _span(0, 200, 10))),
        {"days": (5,)},
    ),
    Subject(
        "password_ok",
        "def f(length, classes):\n"
        "    if length < 8:\n"
        "        return False\n"
        "    if length >= 16:\n"
        "        return classes >= 2\n"
        "    return classes >= 3\n",
        (("length", _span(0, 30)), ("classes", _span(0, 4))),
        {"length": (8, 16), "classes": (2, 3)},
    ),
    Subject(
        "bmi_band",
        "def f(weight, height):\n"
        "    bmi = weight * 10000 // (height * height)\n"
        "    if bmi < 19:\n"
        "        return 'under'\n"
        "    if bmi < 25:\n"
        "        return 'normal'\n"
        "    if bmi < 30:\n"
        "        return 'over'\n"
        "    return 'obese'\n",
        (("weight", _span(30, 150)), ("height", _span(120, 210))),
        {},  # the cut-offs apply to a derived quantity, not to a parameter
    ),
    Subject(
        "seat_price",
        "def f(age, hour, weekend):\n"
        "    price = 12\n"
        "    if age < 12 or age >= 65:\n"
        "        price = 8\n"
        "    if hour < 17 and not weekend:\n"
        "        price = price - 2\n"
        "    return price\n",
        (("age", _span(0, 100)), ("hour", _span(0, 23)), ("weekend", BOOL)),
        {"age": (12, 65), "hour": (17,)},
    ),
    Subject(
        "tax_band",
        "def f(income):\n"
        "    if income <= 50:\n"
        "        return 0\n"
        "    if income <= 100:\n"
        "        return (income - 50) // 5\n"
        "    if income <= 150:\n"
        "        return 10 + (income - 100) // 2\n"
        "    return 35 + (income - 150) // 2\n",
        (("income", _span(0, 200)),),
        {"income": (50, 100, 150)},
    ),
)
