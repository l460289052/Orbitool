from typing import Union, Optional
from . import CalibrationUi
from .manager import Manager
from PyQt5 import QtWidgets, QtCore
from ..utils.formula import Formula
from ..structures.workspace.calibration import Ion


class Widget(QtWidgets.QWidget, CalibrationUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager: Manager = manager
        self.setupUi(self)

        manager.inited.connect(self.init)

    def setupUi(self, Form):
        super().setupUi(Form)

    @property
    def calibration(self):
        return self.manager.workspace.calibration_tab

    def init(self):
        info = self.calibration.info
        ions = ['C5H6O9N-', 'C2HO4-', 'C3H4O7N-']
        for ion in ions:
            info.ions.append(Ion(shown_text=ion, formula=Formula(ion)))

        self.showIons()

    def showIons(self):
        info = self.calibration.info
        table = self.tableWidget
        table.clearContents()
        table.setRowCount(len(info.ions))
        for index, ion in enumerate(info.ions):
            table.setItem(index, 0, QtWidgets.QTableWidgetItem(ion.shown_text))
            table.setItem(
                index, 1, QtWidgets.QTableWidgetItem(format(ion.formula.mass(), ".4f")))

        table.show()
