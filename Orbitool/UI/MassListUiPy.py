from typing import Optional, Union

from PyQt5 import QtCore, QtWidgets

from ..functions.peakfit import masslist as masslist_func
from ..structures.spectrum import MassListItem
from ..utils.formula import Formula
from . import MassListUi
from .manager import Manager, state_node
from .utils import get_tablewidget_selected_row


class Widget(QtWidgets.QWidget, MassListUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        self.manager.inited_or_restored.connect(self.restore)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.addPushButton.clicked.connect(self.addMass)
        self.removePushButton.clicked.connect(self.rmMass)

        # self.mergePushButton.clicked.connect()
        # self.importPushButton.clicked.connect()
        # self.exportPushButton.clicked.connect()

    @property
    def masslist(self):
        return self.manager.workspace.masslist_docker.info

    def restore(self):
        self.showMasslist()

    def showMasslist(self):
        self.doubleSpinBox.setValue(self.masslist.rtol * 1e6)

        table = self.tableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(self.masslist.masslist))
        for index, mass in enumerate(self.masslist.masslist):
            table.setItem(index, 0, QtWidgets.QTableWidgetItem(
                format(mass.position, '.5f')))
            table.setItem(index, 1, QtWidgets.QTableWidgetItem(
                ', '.join(str(f) for f in mass.formulas)))

    @state_node
    def addMass(self):
        text = self.lineEdit.text()
        rtol = self.doubleSpinBox.value() / 1e6
        masslist = self.masslist.masslist
        for item in text.split(','):
            item = item.strip()
            if not item:
                continue
            try:
                mass = float(item)
                masslist_func.addMassTo(
                    masslist, MassListItem(position=mass, formulas=[]), rtol)
            except:
                formula = Formula(item)
                masslist_func.addMassTo(
                    masslist, MassListItem(
                        position=formula.mass(),
                        formulas=[formula]), rtol)
        self.masslist.rtol = rtol

        self.showMasslist()

    @state_node
    def rmMass(self):
        indexes = get_tablewidget_selected_row(self.tableWidget)
        masslist = self.masslist.masslist
        for index in reversed(indexes):
            masslist.pop(index)
        self.showMasslist()

    def get_selected_index(self):
        return get_tablewidget_selected_row(self.tableWidget)
