from gts import experiment
from gts.subjects import SUBJECTS

BY_NAME = {s.name: s for s in SUBJECTS}


def test_a_small_run_is_repeatable_and_has_the_expected_shape():
    subjects = (BY_NAME["grade"], BY_NAME["clamp5"])
    first = experiment.run(subjects, seeds=3, budgets=(4,))
    second = experiment.run(subjects, seeds=3, budgets=(4,))
    assert first == second
    # 2 metrics x 3 baselines per budget
    assert len(first["gains"]) == 2 * 3
    assert {row["baseline"] for row in first["gains"]} == {
        "random, same number of cases", "random, 4x the cases", "two fixed cases (min and max)",
    }
    # the sizes scored: the budget, 4x the budget (random baseline), and the fixed pair
    assert {(r["generator"], r["cases"]) for r in first["scores"]} == {
        ("random", 4), ("random", 16), ("boundary", 4), ("boundary", 16), ("fixed_pair", 2),
    }


def test_every_score_is_a_share():
    result = experiment.run((BY_NAME["discount"],), seeds=2, budgets=(4,))
    assert all(0.0 <= row["mean_over_subjects"] <= 1.0 for row in result["scores"])


def test_the_committed_results_are_what_the_code_produces_now():
    assert experiment._as_text(experiment.run()) == experiment.read()
