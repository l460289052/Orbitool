from typing import Union, Optional
from . import FormulaUi

from PyQt5 import QtWidgets, QtCore
from itertools import chain
from .manager import Manager, state_node
from .component import factory
from ..utils.formula import Formula


class Widget(QtWidgets.QWidget, FormulaUi.Ui_Form):
    def __init__(self, manager: Manager, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.manager = manager
        self.setupUi(self)
        self.manager.inited_or_restored.connect(self.show_or_restore)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.negativeRadioButton.setChecked(True)
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

        if info.polarity == -1:
            self.negativeRadioButton.setChecked(True)
        elif info.polarity == 1:
            self.positiveRadioButton.setChecked(True)

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
            table.setItem(index, 1, QtWidgets.QTableWidgetItem(
                format(Formula(ei).mass(), '.4f')))

    @state_node(withArgs=True)
    def calc(self, force: bool):
        text = self.inputLineEdit.text()
        try:  # number
            info = self.formula.info
            mass = float(text)
            if force:
                result = info.force_calc.get(mass)
            else:
                result = info.restricted_calc.get(mass)
            result.sort(key=lambda f: abs(f.mass() - mass))
            result = ", ".join(str(r) for r in result)
        except:
            mass = Formula(text).mass()
            result = format(mass, '.6f')
        self.resultPlainTextEdit.setPlainText(result)
