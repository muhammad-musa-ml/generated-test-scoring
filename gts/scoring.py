"""Two scores for a suite, a paired bootstrap over subjects, and a relative gain that names its baseline."""
from __future__ import annotations

import random
from statistics import mean


def _indices(analysis, suite) -> list:
    try:
        return [analysis.index[tuple(point)] for point in suite]
    except KeyError as missing:
        raise ValueError(f"input outside the domain of {analysis.subject.name}: {missing}") from None


def mutation_score(analysis, suite) -> float:
    """Share of the killable mutants that at least one input of the suite tells from the original."""
    killable = analysis.killable
    if not killable:
        raise ValueError(f"{analysis.subject.name} has no killable mutant")
    picked = set(_indices(analysis, suite))
    killed = sum(1 for m in killable if analysis.kill_sets[m.number] & picked)
    return killed / len(killable)


def useful_case_rate(analysis, suite) -> float:
    """Share of the suite's inputs that tell at least one mutant from the original (duplicates count)."""
    indices = _indices(analysis, suite)
    if not indices:
        return 0.0
    useful = set()
    for m in analysis.killable:
        useful |= analysis.kill_sets[m.number]
    return sum(1 for i in indices if i in useful) / len(indices)


def relative_gain(candidate: float, baseline: float):
    """(candidate - baseline) / baseline, or None when the baseline is zero (no relative gain exists)."""
    if baseline == 0:
        return None
    return (candidate - baseline) / baseline


def paired_gain(candidate: list, baseline: list, resamples: int = 2000, seed: int = 0):
    """Relative gain of the mean of `candidate` over the mean of `baseline`, one value per subject in
    each list, with a 95% interval from resampling the subjects (the same subjects in both lists)."""
    if len(candidate) != len(baseline) or not candidate:
        raise ValueError("candidate and baseline need one value per subject, in the same order")
    point = relative_gain(mean(candidate), mean(baseline))
    rng = random.Random(seed)
    n = len(candidate)
    draws = []
    for _ in range(resamples):
        pick = [rng.randrange(n) for _ in range(n)]
        gain = relative_gain(mean(candidate[i] for i in pick), mean(baseline[i] for i in pick))
        if gain is not None:
            draws.append(gain)
    if point is None or not draws:
        return point, None, None
    draws.sort()
    low = draws[int(0.025 * (len(draws) - 1))]
    high = draws[int(0.975 * (len(draws) - 1))]
    return point, low, high
