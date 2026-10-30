"""Single-site mutants of a subject's source, and which inputs tell each one from the original.

A mutant is the reference function with exactly one change: a comparison flipped (< to <=), + and -
swapped, * turned into +, and and or swapped, a `not` dropped, or an integer constant moved by one.
Because every subject's domain is small, each mutant is run on every input once. The inputs where its
answer differs from the reference are its kill set. A mutant with an empty kill set behaves like the
original on the whole domain (an equivalent mutant) and is left out of every score.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
from itertools import product

COMPARE_SWAP = {
    ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
}
COMPARE_SYMBOL = {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!="}
ARITH_SWAP = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Add}
ARITH_SYMBOL = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*"}
BOOL_SWAP = {ast.And: ast.Or, ast.Or: ast.And}
BOOL_SYMBOL = {ast.And: "and", ast.Or: "or"}


class _Sites(ast.NodeTransformer):
    """Visits the tree in one fixed order. Without a target it only lists the changes it could make;
    with a target it makes that one change."""

    def __init__(self, target: int | None = None):
        self.target = target
        self.labels: list[str] = []

    def _hit(self, label: str) -> bool:
        index = len(self.labels)
        self.labels.append(label)
        return index == self.target

    def visit_Compare(self, node: ast.Compare):
        self.generic_visit(node)
        if len(node.ops) == 1 and type(node.ops[0]) in COMPARE_SWAP:
            old = type(node.ops[0])
            new = COMPARE_SWAP[old]
            if self._hit(f"{COMPARE_SYMBOL[old]} -> {COMPARE_SYMBOL[new]}"):
                node.ops[0] = new()
        return node

    def visit_BinOp(self, node: ast.BinOp):
        self.generic_visit(node)
        if type(node.op) in ARITH_SWAP:
            old = type(node.op)
            new = ARITH_SWAP[old]
            if self._hit(f"{ARITH_SYMBOL[old]} -> {ARITH_SYMBOL[new]}"):
                node.op = new()
        return node

    def visit_BoolOp(self, node: ast.BoolOp):
        self.generic_visit(node)
        old = type(node.op)
        new = BOOL_SWAP[old]
        if self._hit(f"{BOOL_SYMBOL[old]} -> {BOOL_SYMBOL[new]}"):
            node.op = new()
        return node

    def visit_UnaryOp(self, node: ast.UnaryOp):
        self.generic_visit(node)
        if isinstance(node.op, ast.Not) and self._hit("not dropped"):
            return node.operand
        return node

    def visit_Constant(self, node: ast.Constant):
        if type(node.value) is int:  # a bool is not an integer constant here
            for delta in (1, -1):
                if self._hit(f"{node.value} -> {node.value + delta}"):
                    return ast.copy_location(ast.Constant(node.value + delta), node)
        return node


@dataclass(frozen=True)
class Mutant:
    number: int
    label: str
    source: str


def mutants_of(source: str) -> list[Mutant]:
    """Every distinct single-site mutant of `source`, in tree order."""
    tree = ast.parse(source)
    lister = _Sites()
    lister.visit(copy.deepcopy(tree))
    original = ast.unparse(tree)
    seen = {original}
    out: list[Mutant] = []
    for number, label in enumerate(lister.labels):
        changed = copy.deepcopy(tree)
        changed = _Sites(target=number).visit(changed)
        ast.fix_missing_locations(changed)
        text = ast.unparse(changed)
        if text in seen:
            continue
        seen.add(text)
        out.append(Mutant(number, label, text))
    return out


def load_function(source: str):
    """The function `f` defined by `source`, run with no builtins so a mutant cannot reach anything."""
    namespace: dict = {"__builtins__": {}}
    exec(compile(source, "<subject>", "exec"), namespace)
    return namespace["f"]


def outcome(function, point: tuple) -> str:
    """What the function does on one input, as text, so a changed type or an exception counts too."""
    try:
        return repr(function(*point))
    except Exception as error:  # a mutant may fail where the reference does not
        return "raises " + type(error).__name__


@dataclass
class Analysis:
    """The whole domain of one subject and the exact kill set of each of its mutants."""

    subject: object
    points: list
    index: dict
    mutants: list
    kill_sets: dict  # mutant number -> frozenset of point indices that tell it from the original

    @property
    def killable(self) -> list:
        return [m for m in self.mutants if self.kill_sets[m.number]]

    @property
    def equivalent(self) -> list:
        return [m for m in self.mutants if not self.kill_sets[m.number]]


def analyse(subject) -> Analysis:
    points = list(product(*(values for _, values in subject.params)))
    index = {point: i for i, point in enumerate(points)}
    reference = load_function(subject.source)
    expected = [outcome(reference, p) for p in points]
    bad = [p for p, e in zip(points, expected) if e.startswith("raises")]
    if bad:
        raise ValueError(f"{subject.name}: the reference raises on {bad[0]}")
    mutants = mutants_of(subject.source)
    kill_sets = {}
    for mutant in mutants:
        function = load_function(mutant.source)
        kill_sets[mutant.number] = frozenset(
            i for i, p in enumerate(points) if outcome(function, p) != expected[i]
        )
    return Analysis(subject, points, index, mutants, kill_sets)
