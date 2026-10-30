# generated-test-scoring

Scores a test suite by how many seeded faults it catches, and reports a suite's gain together with the
baseline it is measured against.

A percentage gain for generated tests means little until three things are stated: the score, the unit it
is counted in, and what it is compared with. This repository makes all three explicit on a case small
enough to check by hand, and shows how far one fixed set of suites moves when only the baseline or the
score changes.

## What it does

- Ten small subjects. Each is a reference function (a grade table, shipping tiers, a leap-year rule and
  so on) with a small input domain, so every input can be run.
- Mutants. Each subject is copied with exactly one change: a comparison flipped (`<` to `<=`), `+` and `-`
  swapped, `*` turned into `+`, `and` and `or` swapped, a `not` dropped, or an integer constant moved by
  one. Every mutant is run on every input. A mutant whose answers never differ from the original is
  equivalent and is left out of all scores: 150 killable and 18 equivalent mutants here.
- Three ways to pick inputs: random inputs from the whole domain; boundary inputs, which use only the
  thresholds the subject's spec states (each threshold as t-1, t and t+1) plus the smallest and largest
  value of each parameter; and a fixed pair, all parameters at their minimum and then all at their
  maximum. Any other source of inputs (a model, a person) can be scored by returning a list of inputs.
- Two scores. The mutation score is the share of killable mutants that at least one input of the suite
  tells from the original. The useful-case rate is the share of the suite's inputs that tell at least one
  mutant from the original; repeated inputs count.
- A comparison of the boundary suites with three baselines, with a 95% interval from resampling the ten
  subjects (the same subjects on both sides of each comparison).

## Result

Each cell is the mean over 10 subjects of a share (the subject's score averaged over 200 seeds; the fixed
pair has no seeds). The relative gain is the boundary mean minus the baseline mean, divided by the baseline
mean, so it compares average shares and not fault counts. The boundary suites have 8 cases:

| score | baseline | baseline mean | boundary mean, 8 cases | relative gain (95% interval) |
|---|---|---|---|---|
| mutation score | random, 8 cases | 0.519 | 0.731 | +40.9% (21.1 to 72.6) |
| mutation score | random, 32 cases | 0.708 | 0.731 | +3.2% (-13.1 to 21.6) |
| mutation score | two fixed cases (min and max) | 0.370 | 0.731 | +97.5% (59.7 to 178.9) |
| useful-case rate | random, 8 cases | 0.809 | 0.824 | +1.8% (-10.1 to 21.1) |
| useful-case rate | random, 32 cases | 0.810 | 0.824 | +1.8% (-10.1 to 21.2) |
| useful-case rate | two fixed cases (min and max) | 0.800 | 0.824 | +3.0% (-15.8 to 35.0) |

The same 8 boundary cases are about twice as good as two fixed cases (min and max), 41% better than 8 random
cases, 3% better than 32 random cases (an interval that includes zero), and 2% better on the share of
useful cases. Each of those is a true statement about the same suites, and only the first one reads as a
large improvement. The files in `results/` also hold the 4-case and 16-case rows; at 4 boundary cases the
mutation score is 17.0% below 16 random cases.

## Limits

- The faults are the ones the operators above can make, not defects found in use. The equivalence check is
  exact only because every domain is small (41 to 11,011 inputs).
- The expected answer of every case is taken from the reference function, so a wrong expected value in a
  generated test is not scored here.
- Ten subjects written for this repository, so the intervals are wide. The boundary generator reads only
  thresholds on a parameter; the cut-offs of `bmi_band` apply to a derived value, so it cannot target them.
  It has 4 boundary candidates, so its 8-case boundary suite is those 4 plus 4 random cases; the other nine
  subjects have 8 or more candidates.
- The generators are rules, not language models.

## Run it

Developed and tested on Python 3.13; `pyproject.toml` says 3.10 or later, which I have not run. Only the
tests need a package.

```
python -m pip install -r requirements-dev.txt
python -m pytest -q            # 72 tests, about 20 seconds
python -m gts.experiment       # rewrites results/
python -m gts.experiment --check   # fails if results/ no longer matches the code
```

The harness's own tests were checked by changing the code in a scratch copy: 10 hand-made changes (an
off-by-one denominator, duplicates no longer counted, a dropped threshold neighbour and others), and the
unit tests failed on each of the 10, apart from the test that compares `results/` with a fresh run.

## Layout

```
gts/subjects.py     the ten reference functions, their domains and spec thresholds
gts/mutants.py      single-site mutants, exact kill sets, equivalent mutants
gts/generators.py   random, boundary and the fixed pair
gts/scoring.py      the two scores, relative gain, paired bootstrap over subjects
gts/experiment.py   the experiment behind results/
tests/              pytest
results/            scores.csv, gains.csv, meta.json (counts and settings)
```
