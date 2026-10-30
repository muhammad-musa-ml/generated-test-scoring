import random

import pytest

from conftest import tiny
from gts.mutants import analyse
from gts.scoring import mutation_score, paired_gain, relative_gain, useful_case_rate
from gts.subjects import SUBJECTS

# f(x) = x < 3 on 0..6 has three killable mutants: 3 -> 4 (told apart at x=3), 3 -> 2 (at x=2), < -> <= (at x=3)
THRESHOLD = tiny("def f(x):\n    return x < 3\n", range(7))


@pytest.mark.parametrize("name", [s.name for s in SUBJECTS])
def test_running_every_input_kills_every_killable_mutant(analyses, name):
    analysis = analyses[name]
    assert mutation_score(analysis, analysis.points) == 1.0


@pytest.mark.parametrize("name", [s.name for s in SUBJECTS])
def test_an_empty_suite_scores_zero(analyses, name):
    assert mutation_score(analyses[name], []) == 0.0
    assert useful_case_rate(analyses[name], []) == 0.0


def test_scores_on_a_hand_checkable_subject():
    analysis = analyse(THRESHOLD)
    assert len(analysis.killable) == 3
    assert mutation_score(analysis, [(3,)]) == pytest.approx(2 / 3)
    assert mutation_score(analysis, [(2,)]) == pytest.approx(1 / 3)
    assert mutation_score(analysis, [(2,), (3,)]) == 1.0
    assert mutation_score(analysis, [(0,), (6,)]) == 0.0
    assert mutation_score(analysis, [(3,), (3,), (3,)]) == pytest.approx(2 / 3)  # repeating a case adds nothing


def test_useful_case_rate_counts_duplicates_and_useless_cases():
    analysis = analyse(THRESHOLD)
    assert useful_case_rate(analysis, [(0,), (3,), (3,)]) == pytest.approx(2 / 3)
    assert useful_case_rate(analysis, [(2,)]) == 1.0
    assert useful_case_rate(analysis, [(0,), (6,)]) == 0.0


def test_a_larger_suite_never_scores_lower(analyses):
    rng = random.Random(7)
    for name in ("seat_price", "tax_band", "late_fee"):
        analysis = analyses[name]
        order = rng.sample(analysis.points, 30)
        scores = [mutation_score(analysis, order[:k]) for k in range(31)]
        assert scores == sorted(scores), name


def test_an_input_outside_the_domain_is_refused():
    with pytest.raises(ValueError, match="outside the domain"):
        mutation_score(analyse(THRESHOLD), [(99,)])


def test_relative_gain_is_undefined_for_a_zero_baseline():
    assert relative_gain(0.5, 0.0) is None
    assert relative_gain(15, 10) == pytest.approx(0.5)
    assert relative_gain(5, 10) == pytest.approx(-0.5)


def test_paired_gain_of_a_constant_ratio_has_a_degenerate_interval():
    baseline = [0.2, 0.4, 0.6, 0.8]
    candidate = [1.5 * b for b in baseline]
    point, low, high = paired_gain(candidate, baseline)
    assert point == pytest.approx(0.5)
    assert low == pytest.approx(0.5) and high == pytest.approx(0.5)


def test_paired_gain_interval_brackets_the_point_and_is_repeatable():
    baseline = [0.3, 0.5, 0.2, 0.7, 0.4, 0.6]
    candidate = [0.5, 0.6, 0.4, 0.7, 0.9, 0.6]
    first = paired_gain(candidate, baseline, seed=3)
    assert first == paired_gain(candidate, baseline, seed=3)
    point, low, high = first
    assert low < point < high


def test_paired_gain_with_an_all_zero_baseline_has_no_gain_and_no_interval():
    assert paired_gain([0.1, 0.2], [0.0, 0.0]) == (None, None, None)


def test_paired_gain_refuses_unpaired_lists():
    with pytest.raises(ValueError):
        paired_gain([0.1, 0.2], [0.1])
    with pytest.raises(ValueError):
        paired_gain([], [])
