import ast
import random

import pytest

from conftest import tiny
from gts.generators import boundary_inputs, boundary_values, domain_points, fixed_pair, random_inputs
from gts.subjects import SUBJECTS, Subject

BY_NAME = {s.name: s for s in SUBJECTS}


def int_constants(source):
    return {abs(n.value) for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Constant) and type(n.value) is int}


@pytest.mark.parametrize("subject", SUBJECTS, ids=lambda s: s.name)
def test_every_spec_threshold_is_a_constant_in_the_reference(subject):
    constants = int_constants(subject.source)
    for name, thresholds in subject.thresholds.items():
        assert name in dict(subject.params), (subject.name, name)
        for t in thresholds:
            assert abs(t) in constants, (subject.name, name, t)


def test_random_inputs_are_distinct_in_the_domain_and_repeatable():
    subject = BY_NAME["seat_price"]
    domain = set(domain_points(subject))
    first = random_inputs(subject, 12, random.Random(1))
    assert len(first) == 12 and len(set(first)) == 12 and set(first) <= domain
    assert first == random_inputs(subject, 12, random.Random(1))
    assert first != random_inputs(subject, 12, random.Random(2))


def test_random_inputs_never_exceed_the_domain():
    subject = tiny("def f(x):\n    return x\n", range(3))
    assert sorted(random_inputs(subject, 10, random.Random(0))) == [(0,), (1,), (2,)]


def test_boundary_values_hold_both_edges_and_each_threshold_with_its_neighbours():
    values = dict(zip([n for n, _ in BY_NAME["grade"].params], boundary_values(BY_NAME["grade"])))
    assert values["score"] == [0, 59, 60, 61, 69, 70, 71, 79, 80, 81, 89, 90, 91, 100]


def test_a_parameter_without_thresholds_gets_only_its_edges_and_a_flag_gets_both_values():
    shipping = boundary_values(BY_NAME["shipping_fee"])
    assert shipping[0] == [0, 4, 5, 6, 19, 20, 21, 60]
    assert shipping[1] == [False, True]
    assert boundary_values(BY_NAME["bmi_band"]) == [[30, 150], [120, 210]]


def test_threshold_neighbours_outside_the_domain_are_dropped():
    subject = Subject("edge", "def f(x):\n    return x < 0\n", (("x", (0, 1, 2)),), {"x": (0,)})
    assert boundary_values(subject) == [[0, 1, 2]]


@pytest.mark.parametrize("name", ["grade", "seat_price", "password_ok"])
def test_boundary_inputs_come_from_the_candidates_and_have_the_requested_size(name):
    subject = BY_NAME[name]
    candidates = set()
    from itertools import product
    candidates.update(product(*boundary_values(subject)))
    picked = boundary_inputs(subject, 6, random.Random(5))
    assert len(picked) == 6 and len(set(picked)) == 6 and set(picked) <= candidates
    assert picked == boundary_inputs(subject, 6, random.Random(5))


def test_when_the_budget_exceeds_the_candidates_the_rest_comes_from_the_wider_domain():
    subject = BY_NAME["bmi_band"]  # only 2 x 2 = 4 candidates
    picked = boundary_inputs(subject, 10, random.Random(0))
    assert len(picked) == 10 and len(set(picked)) == 10
    assert set(picked) <= set(domain_points(subject))
    from itertools import product
    assert set(product(*boundary_values(subject))) <= set(picked)


def test_the_fixed_pair_is_the_minimum_and_the_maximum():
    assert fixed_pair(BY_NAME["shipping_fee"]) == [(0, False), (60, True)]
    assert fixed_pair(BY_NAME["clamp5"]) == [(-20,), (20,)]
