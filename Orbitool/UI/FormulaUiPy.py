from typing import Union, Optional
from . import FormulaUi

from PyQt5 import QtWidgets, QtCore
from itertools import chain
from .manager import Manager, state_node
from .component import factory
from ..utils.formula import Formula
from .utils import get_tablewidget_selected_row
from . import FormulaResultUiPy


class Widget(QtWidgets.QWidget, FormulaUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        self.manager.init_or_restored.connect(self.show_or_restore)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.elementAddToolButton.clicked.connect(self.restrictedAddElement)
        self.isotopeAddToolButton.clicked.connect(self.restrictedAddIsotope)
        self.isotopeDelToolButton.clicked.connect(self.restrictedDelIsotopes)

        self.unrestrictedAddToolButton.clicked.connect(self.forceAdd)
        self.unrestrictedDelToolButton.clicked.connect(self.forceDel)

        self.applyPushButton.clicked.connect(self.applyChange)

        self.calcPushButton.clicked.connect(lambda: self.calc(False))
        self.forcePushButton.clicked.connect(lambda: self.calc(True))

    @property
    def formula(self):
        return self.manager.workspace.formula_docker

    def show_or_restore(self):
        self.showUnify()
        self.showRestricted()
        self.showForce()

    def showUnify(self):
        info = self.formula.info

        self.baseGroupLineEdit.setText(str(info.base_group))

        self.mzMinDoubleSpinBox.setValue(info.mz_min)
        self.mzMaxDoubleSpinBox.setValue(info.mz_max)

        self.rtolDoubleSpinBox.setValue(info.rtol * 1e6)

    def showRestricted(self):
        calc = self.formula.info.restricted_calc

        self.dbeMinDoubleSpinBox.setValue(calc.DBEMin)
        self.dbeMaxDoubleSpinBox.setValue(calc.DBEMax)
        self.nitrogenRuleCheckBox.setChecked(calc.nitrogenRule)

        usedElements = set(calc.getElements())

        element_table = self.elementTableWidget
        element_table.clearContents()
        element_table.setRowCount(0)
        inited_elements = calc.getInitedElements()
        element_table.setRowCount(len(inited_elements))
        inited_elements = list(chain(usedElements, set(
            inited_elements) - usedElements))
        for index in range(len(inited_elements)):
            if inited_elements[index].startswith('e'):
                inited_elements.insert(0, inited_elements.pop(index))
        for index, e in enumerate(inited_elements):
            params = calc[e]

            element_table.setItem(index, 0, QtWidgets.QTableWidgetItem(e))
            element_table.setCellWidget(
                index, 1, factory.CheckBoxFactory(e in usedElements or e.startswith('e')))

            for column, s in enumerate([
                    format(Formula(e if not e.startswith(
                        'e') else '-').mass(), '.4f'),
                    str(params["Min"]),
                    str(params["Max"]),
                    str(params["DBE2"]),
                    str(params["HMin"]),
                    str(params["HMax"]),
                    str(params["OMin"]),
                    str(params["OMax"])], 2):
                element_table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(s))

        isotope_table = self.isotopeTableWidget
        isotope_table.clearContents()
        isotope_table.setRowCount(0)
        isotopes = calc.getIsotopes()
        isotope_table.setRowCount(len(isotopes))

        for index, isotope in enumerate(isotopes):
            isotope_table.setItem(
                index, 0, QtWidgets.QTableWidgetItem(isotope))
            isotope_table.setItem(
                index, 1,
                QtWidgets.QTableWidgetItem(format(Formula(isotope).mass(), '.4f')))

    def showForce(self):
        calc = self.formula.info.force_calc
        table = self.unrestrictedTableWidget
        table.clearContents()
        table.setRowCount(0)
        ei_list = calc.getEIList()
        table.setRowCount(len(ei_list))
        for index, ei in enumerate(ei_list):
            table.setItem(index, 0, QtWidgets.QTableWidgetItem(ei))
            table.setItem(index, 1, QtWidgets.QTableWidgetItem(str(calc[ei])))

    @state_node(withArgs=True)
    def calc(self, force: bool):
        text = self.inputLineEdit.text()

        manager = self.manager
        if manager.formulas_result_win is not None:
            manager.formulas_result_win.close()
            del manager.formulas_result_win
        manager.formulas_result_win = FormulaResultUiPy.Window.FactoryCalc(
            manager, text, force)
        manager.formulas_result_win.show()

    @state_node
    def restrictedAddElement(self):
        element = self.elementLineEdit.text().strip()
        if element in self.formula.info.restricted_calc.getInitedElements():
            return

        element = Formula(element)

        table = self.elementTableWidget
        row = table.rowCount()
        table.setRowCount(row + 1)

        table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(element)))
        table.setCellWidget(row, 1, factory.CheckBoxFactory(False))
        contents = [format(element.mass(), '.4f'),
                    0, 0, 0, 0, 0, 0, 0]

        for column, s in enumerate(contents, 2):
            table.setItem(row, column, QtWidgets.QTableWidgetItem(str(s)))

    @state_node
    def restrictedAddIsotope(self):
        isotope = self.isotopeLineEdit.text().strip()
        if isotope in self.formula.info.restricted_calc.getIsotopes():
            return

        isotope = Formula(isotope)

        table = self.isotopeTableWidget
        row = table.rowCount()
        table.setRowCount(row + 1)

        table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(isotope)))
        table.setItem(row, 1, QtWidgets.QTableWidgetItem(
            format(isotope.mass(), '.4f')))

    @state_node
    def restrictedDelIsotopes(self):
        table = self.isotopeTableWidget
        indexes = get_tablewidget_selected_row(table)
        for index in reversed(indexes):
            table.removeRow(index)

    @state_node
    def forceAdd(self):
        element = self.unrestrictedLineEdit.text().strip()
        if element in self.formula.info.force_calc.getEIList():
            return

        element = Formula(element)

        table = self.unrestrictedTableWidget
        row = table.rowCount()
        table.setRowCount(row + 1)

        table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(element)))
        table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(999)))

    @state_node
    def forceDel(self):
        table = self.unrestrictedTableWidget
        indexes = get_tablewidget_selected_row(table)
        for index in reversed(indexes):
            table.removeRow(index)

    @state_node
    def applyChange(self):
        info = self.formula.info
        calc = info.restricted_calc
        force_calc = info.force_calc
        info.base_group = Formula(self.baseGroupLineEdit.text())

        calc.MMin = info.mz_min = self.mzMinDoubleSpinBox.value()
        calc.MMax = info.mz_max = self.mzMaxDoubleSpinBox.value()

        force_calc.rtol = calc.rtol = info.rtol = self.rtolDoubleSpinBox.value() * 1e-6

        # restricted
        calc.DBEMin = self.dbeMinDoubleSpinBox.value()
        calc.DBEMax = self.dbeMaxDoubleSpinBox.value()
        calc.nitrogenRule = self.nitrogenRuleCheckBox.isChecked()

        table = self.elementTableWidget

        for row in range(table.rowCount()):
            e = table.item(row, 0).text()
            used = table.cellWidget(row, 1).isChecked()
            if not e.startswith('e'):
                calc.setEI(e, used)
            params = {
                "Min": int(table.item(row, 3).text()),
                "Max": int(table.item(row, 4).text()),
                "DBE2": float(table.item(row, 5).text()),
                "HMin": float(table.item(row, 6).text()),
                "HMax": float(table.item(row, 7).text()),
                "OMin": float(table.item(row, 8).text()),
                "OMax": float(table.item(row, 9).text())}
            calc[e] = params

        for isotope in calc.getIsotopes():
            calc.setEI(isotope, False)

        table = self.isotopeTableWidget
        for row in range(table.rowCount()):
            i = table.item(row, 0).text()
            calc.setEI(i)

        calc.clear()

        table = self.unrestrictedTableWidget
        nums = {ei: -1 for ei in force_calc.getEIList()}
        for row in range(table.rowCount()):
            nums[table.item(row, 0).text()] = int(table.item(row, 1).text())

        for ei, num in nums.items():
            force_calc[ei] = num

        self.show_or_restore()
