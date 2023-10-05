from ..masslist import MassListItem, MassListHelper
from ...formula import Formula


def test_mergeinto():
    masslist = [MassListItem(position=i) for i in range(1, 10)]

    MassListHelper.mergeInto(masslist, [MassListItem(
        position=i + 1e-7, formulas=[]) for i in range(1, 20)], 1e-6)

    assert len(masslist) == 19


def test_formula():
    f = Formula('CH4')
    masslist = []

    MassListHelper.addMassTo(masslist, MassListItem(position=f.mass()), 1e-6)

    MassListHelper.addMassTo(masslist, MassListItem(position=f.mass(), formulas=[f]), 1e-6)
    MassListHelper.addMassTo(masslist, MassListItem(position=1), 1e-6)
    MassListHelper.addMassTo(masslist, MassListItem(position=1000), 1e-6)
    assert len(masslist) == 3
    assert masslist[0].position == 1.
    assert masslist[1].formulas[0] == f
    assert masslist[2].position == 1000.
