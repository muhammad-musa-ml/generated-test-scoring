"""Run the experiment and write results/.

    python -m gts.experiment            writes results/scores.csv, results/gains.csv, results/meta.json
    python -m gts.experiment --check    runs again and fails if the committed results differ

For every subject, generator, budget and seed it builds a suite, scores it, and averages over the seeds.
It then compares the boundary generator with three baselines on both scores, one row per budget.
"""
from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path
from statistics import mean

from gts import generators
from gts.mutants import analyse
from gts.scoring import mutation_score, paired_gain, useful_case_rate
from gts.subjects import SUBJECTS

SEEDS = 200
BUDGETS = (4, 8, 16)
BASELINE_FACTOR = 4  # the "more tests" baseline gets this many times the budget
METRICS = {"mutation_score": mutation_score, "useful_case_rate": useful_case_rate}
RESULTS = Path(__file__).resolve().parent.parent / "results"


def _suite(subject, generator: str, n: int, seed: int) -> list:
    rng = random.Random(f"{subject.name}|{generator}|{n}|{seed}")
    if generator == "random":
        return generators.random_inputs(subject, n, rng)
    if generator == "boundary":
        return generators.boundary_inputs(subject, n, rng)
    raise ValueError(generator)


def run(subjects=SUBJECTS, seeds: int = SEEDS, budgets=BUDGETS) -> dict:
    """Return {'scores': rows, 'gains': rows, 'meta': dict}; nothing is written."""
    analyses = [analyse(s) for s in subjects]
    sizes = sorted({n for b in budgets for n in (b, b * BASELINE_FACTOR)})
    # per[(metric, generator, n)] -> one value per subject, the mean over seeds
    per: dict = {}
    for analysis in analyses:
        subject = analysis.subject
        for generator in ("random", "boundary"):
            for n in sizes:
                for metric_name, metric in METRICS.items():
                    values = [metric(analysis, _suite(subject, generator, n, seed)) for seed in range(seeds)]
                    per.setdefault((metric_name, generator, n), []).append(mean(values))
        pair = generators.hand_pair(subject)
        for metric_name, metric in METRICS.items():
            per.setdefault((metric_name, "hand_pair", 2), []).append(metric(analysis, pair))

    score_rows = []
    for (metric_name, generator, n), values in sorted(per.items()):
        score_rows.append({"metric": metric_name, "generator": generator, "cases": n,
                           "mean_over_subjects": round(mean(values), 4)})

    gain_rows = []
    for budget in budgets:
        baselines = (
            ("random, same number of cases", "random", budget),
            (f"random, {BASELINE_FACTOR}x the cases", "random", budget * BASELINE_FACTOR),
            ("two hand-written cases (min and max)", "hand_pair", 2),
        )
        for metric_name in METRICS:
            candidate = per[(metric_name, "boundary", budget)]
            for label, generator, n in baselines:
                baseline = per[(metric_name, generator, n)]
                point, low, high = paired_gain(candidate, baseline)
                gain_rows.append({
                    "metric": metric_name, "boundary_cases": budget, "baseline": label,
                    "baseline_mean": round(mean(baseline), 4), "boundary_mean": round(mean(candidate), 4),
                    "relative_gain": _pct(point), "ci95_low": _pct(low), "ci95_high": _pct(high),
                })

    meta = {
        "subjects": len(analyses), "seeds": seeds, "budgets": list(budgets), "baseline_factor": BASELINE_FACTOR,
        "mutants": {a.subject.name: {"killable": len(a.killable), "equivalent": len(a.equivalent),
                                     "domain_size": len(a.points)} for a in analyses},
    }
    return {"scores": score_rows, "gains": gain_rows, "meta": meta}


def _pct(value):
    return "" if value is None else f"{value * 100:.1f}"


def _write_csv(path: Path, rows: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write(result: dict, folder: Path = RESULTS) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    _write_csv(folder / "scores.csv", result["scores"])
    _write_csv(folder / "gains.csv", result["gains"])
    text = json.dumps(result["meta"], indent=2, sort_keys=True) + "\n"
    (folder / "meta.json").write_text(text, encoding="utf-8", newline="\n")


def read(folder: Path = RESULTS) -> dict:
    out = {}
    for name in ("scores", "gains"):
        with open(folder / f"{name}.csv", newline="", encoding="utf-8") as handle:
            out[name] = list(csv.DictReader(handle))
    out["meta"] = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    return out


def _as_text(result: dict) -> dict:
    """The rows as the CSV files hold them (all text), so a fresh run compares with a file read back."""
    return {
        "scores": [{k: str(v) for k, v in row.items()} for row in result["scores"]],
        "gains": [{k: str(v) for k, v in row.items()} for row in result["gains"]],
        "meta": result["meta"],
    }


def main(argv: list) -> int:
    fresh = run()
    if "--check" in argv:
        committed = read()
        if _as_text(fresh) == committed:
            print(f"results match: {len(committed['scores'])} score rows, {len(committed['gains'])} gain rows")
            return 0
        print("results differ from the committed files", file=sys.stderr)
        return 1
    write(fresh)
    print(f"wrote {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
