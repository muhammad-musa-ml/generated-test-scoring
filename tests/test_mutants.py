import ast

import pytest

from conftest import tiny
from gts.mutants import analyse, load_function, mutants_of, outcome
from gts.subjects import SUBJECTS


def labels_and_sources(source):
    return [(m.label, m.source) for m in mutants_of(source)]


def test_comparison_and_constant_mutants_are_exactly_these():
    # children are visited before their parent, so the constant's two changes come before the operator's
    assert labels_and_sources("def f(x):\n    return x < 3\n") == [
        ("3 -> 4", "def f(x):\n    return x < 4"),
        ("3 -> 2", "def f(x):\n    return x < 2"),
        ("< -> <=", "def f(x):\n    return x <= 3"),
    ]


@pytest.mark.parametrize("body, expected_labels", [
    ("return a + b", ["+ -> -"]),
    ("return a - b", ["- -> +"]),
    ("return a * b", ["* -> +"]),
    ("return a and b", ["and -> or"]),
    ("return a or b", ["or -> and"]),
    ("return not a", ["not dropped"]),
    ("return a == b", ["== -> !="]),
    ("return a != b", ["!= -> =="]),
    ("return a >= b", [">= -> >"]),
    ("return a > b", ["> -> >="]),
    ("return a <= b", ["<= -> <"]),
])
def test_each_operator_family_has_its_one_change(body, expected_labels):
    source = f"def f(a, b):\n    {body}\n"
    assert [m.label for m in mutants_of(source)] == expected_labels


def test_negative_constants_move_the_magnitude_and_keep_the_sign():
    sources = [m.source for m in mutants_of("def f(x):\n    return -5\n")]
    assert sources == ["def f(x):\n    return -6", "def f(x):\n    return -4"]


def test_booleans_are_not_integer_constants():
    assert mutants_of("def f(x):\n    return True\n") == []


def test_chained_comparisons_get_no_operator_mutant():
    labels = [m.label for m in mutants_of("def f(x):\n    return 0 < x < 9\n")]
    assert labels == ["0 -> 1", "0 -> -1", "9 -> 10", "9 -> 8"]


def test_every_shipped_mutant_is_valid_distinct_and_different_from_the_original():
    for subject in SUBJECTS:
        mutants = mutants_of(subject.source)
        sources = [m.source for m in mutants]
        assert len(set(sources)) == len(sources), subject.name
        for text in sources:
            load_function(text)  # compiles and defines f
        assert ast.unparse(ast.parse(subject.source)) not in sources, subject.name


def test_equivalent_mutants_are_told_from_killable_ones_exactly():
    analysis = analyse(tiny("def f(x):\n    return x > 0\n", (1, 2, 3, 4, 5)))
    assert {m.label for m in analysis.equivalent} == {"> -> >=", "0 -> -1"}
    assert {m.label for m in analysis.killable} == {"0 -> 1"}
    only = analysis.killable[0]
    assert analysis.kill_sets[only.number] == frozenset({analysis.index[(1,)]})


def test_a_mutant_that_raises_where_the_reference_does_not_is_killed_there():
    analysis = analyse(tiny("def f(x):\n    return 10 // (x + 1)\n", (0, 1, 2, 3)))
    swapped = [m for m in analysis.mutants if m.label == "+ -> -"][0]
    assert analysis.index[(1,)] in analysis.kill_sets[swapped.number]
    assert outcome(load_function(swapped.source), (1,)) == "raises ZeroDivisionError"


def test_a_reference_that_raises_on_its_own_domain_is_refused():
    with pytest.raises(ValueError, match="reference raises"):
        analyse(tiny("def f(x):\n    return 1 // x\n", (0, 1)))


def test_the_function_runs_without_builtins():
    function = load_function("def f(x):\n    return len([x])\n")
    assert outcome(function, (1,)) == "raises NameError"
