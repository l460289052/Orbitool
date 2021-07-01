from typing import Union, Optional
from . import CalibrationUi
from .manager import Manager, state_node
from PyQt5 import QtWidgets, QtCore
from ..utils.formula import Formula
from ..structures.workspace.calibration import Ion
from .utils import get_tablewidget_selected_row


class Widget(QtWidgets.QWidget, CalibrationUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager: Manager = manager
        self.setupUi(self)

        manager.inited.connect(self.init)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.addIonToolButton.clicked.connect(self.addIon)
        self.delIonToolButton.clicked.connect(self.removeIon)

    @property
    def calibration(self):
        return self.manager.workspace.calibration_tab

    def init(self):
        ions = ['C5H6O9N-', 'C2HO4-', 'C3H4O7N-']
        self.calibration.info.add_ions(ions)
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

    @state_node
    def addIon(self):
        self.calibration.info.add_ions(self.ionLineEdit.text().split(','))
        self.showIons()

    @state_node
    def removeIon(self):
        indexes = get_tablewidget_selected_row(self.tableWidget)
        ions = self.calibration.info.ions
        for index in reversed(indexes):
            ions.pop(index)
        self.showIons()
