from typing import List

from Orbitool.base import BaseRowStructure
from ..formula import Formula, FormulaList, FormulaType
from Orbitool.utils.binary_search import indexNearest, indexFirstBiggerThan


class MassListItem(BaseRowStructure):
    position: float
    formulas: FormulaList = []


class MassListHelper:
    @classmethod
    def get_position(cls, l: List[MassListItem], index: int):
        return l[index].position

    @classmethod
    def addMassTo(cls, original_list: List[MassListItem], new_item: MassListItem, rtol: float):
        if len(new_item.formulas) == 1:
            new_item.position = new_item.formulas[0].mass()
        if len(original_list) == 0:
            original_list.append(new_item)
            return
        insert_index = indexFirstBiggerThan(
            original_list, new_item.position, method=cls.get_position)
        index = indexNearest(
            original_list, new_item.position, method=cls.get_position)

        item = original_list[index]

        if abs(item.position / new_item.position - 1) > rtol:
            original_list.insert(insert_index, new_item)
            return

        if set(item.formulas) == set(new_item.formulas):
            return

        if len(new_item.formulas) == 0:
            return

        if len(item.formulas) == 0:
            original_list[index] = new_item
            return

        original_list.insert(insert_index, new_item)

    @classmethod
    def mergeInto(cls, original_list: List[MassListItem], new_list: List[MassListItem], rtol: float):
        for item in new_list:
            cls.addMassTo(original_list, item, rtol)

    @classmethod
    def fitUseMassList(cls, position: float, masslist: List[MassListItem], rtol: float) -> List[Formula]:
        if len(masslist) == 0:
            return []
        index = indexNearest(masslist, position, method=cls.get_position)
        item = masslist[index]
        if abs(item.position / position - 1) < rtol:
            return item.formulas
        return []
