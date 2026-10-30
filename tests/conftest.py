import pytest

from gts.mutants import analyse
from gts.subjects import SUBJECTS, Subject


@pytest.fixture(scope="session")
def analyses():
    """Every shipped subject analysed once: name -> Analysis."""
    return {s.name: analyse(s) for s in SUBJECTS}


def tiny(source, values, name="tiny"):
    """A one-parameter subject for exact, hand-checkable cases."""
    return Subject(name, source, (("x", tuple(values)),), {})
