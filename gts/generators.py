"""Three ways to pick test inputs. Any other generator (a model, a person) only has to return inputs.

random_inputs     n inputs drawn uniformly from the whole domain, ignoring the spec.
boundary_inputs   n inputs drawn from the spec's boundary values: each stated threshold t as t-1, t and
                  t+1, plus the smallest and largest value of every parameter.
hand_pair         the same two inputs every time: all parameters at their smallest value, then all at
                  their largest. It stands for a tester who writes a minimum case and a maximum case.
"""
from __future__ import annotations

import random
from itertools import product


def domain_points(subject) -> list:
    return list(product(*(values for _, values in subject.params)))


def random_inputs(subject, n: int, rng: random.Random) -> list:
    points = domain_points(subject)
    return rng.sample(points, min(n, len(points)))


def boundary_values(subject) -> list:
    """Per parameter, the values the boundary generator may use."""
    out = []
    for name, values in subject.params:
        chosen = {values[0], values[-1]}
        for t in subject.thresholds.get(name, ()):
            chosen.update(v for v in (t - 1, t, t + 1) if v in values)
        out.append(sorted(chosen, key=values.index))
    return out


def boundary_inputs(subject, n: int, rng: random.Random) -> list:
    candidates = list(product(*boundary_values(subject)))
    if n <= len(candidates):
        return rng.sample(candidates, n)
    rest = [p for p in domain_points(subject) if p not in set(candidates)]
    return candidates + rng.sample(rest, min(n - len(candidates), len(rest)))


def hand_pair(subject) -> list:
    low = tuple(values[0] for _, values in subject.params)
    high = tuple(values[-1] for _, values in subject.params)
    return [low, high]
