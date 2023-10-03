import csv
from typing import Optional, Union
from functools import partial

from PyQt6 import QtCore, QtWidgets

from Orbitool.models.peakfit import MassListItem, MassListHelper
from Orbitool.models.formula import Formula
from . import MassListUi
from .manager import Manager, state_node
from .utils import get_tablewidget_selected_row, openfile, savefile


class Widget(QtWidgets.QWidget):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.ui = MassListUi.Ui_Form()
        self.setupUi()
        manager.getters.mass_list_selected_indexes.connect(
            self.get_selected_index)
        self.manager.init_or_restored.connect(self.restore)

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)

        ui.doubleSpinBox.valueChanged.connect(self.updateRtol)

        ui.addPushButton.clicked.connect(self.addMass)
        ui.removePushButton.clicked.connect(self.rmMass)

        ui.groupPlusPushButton.clicked.connect(lambda: self.group_plus(1))
        ui.groupMinusPushButton.clicked.connect(lambda: self.group_plus(-1))

        ui.mergePushButton.clicked.connect(self.merge)
        ui.importPushButton.clicked.connect(self.import_masslist)
        ui.exportPushButton.clicked.connect(self.export)

    @property
    def info(self):
        return self.manager.workspace.info.masslist_docker

    def restore(self):
        self.showMasslist()
        self.info.ui_state.restore_state(self.ui)

    def updateState(self):
        self.info.ui_state.store_state(self.ui)

    def showMasslist(self):
        ui = self.ui
        ui.doubleSpinBox.setValue(self.info.rtol * 1e6)

        table = ui.tableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(self.info.masslist))
        for index, mass in enumerate(self.info.masslist):
            table.setItem(index, 0, QtWidgets.QTableWidgetItem(
                format(mass.position, '.5f')))
            table.setItem(index, 1, QtWidgets.QTableWidgetItem(
                ', '.join(str(f) for f in mass.formulas)))

    @state_node
    def updateRtol(self):
        self.info.rtol = self.ui.doubleSpinBox.value() * 1e-6

    @state_node
    def addMass(self):
        ui = self.ui
        text = ui.addItemLineEdit.text()
        rtol = self.info.rtol
        masslist = self.info.masslist
        for item in text.split(','):
            item = item.strip()
            if not item:
                continue
            try:
                mass = float(item)
                MassListHelper.addMassTo(
                    masslist, MassListItem(mass), rtol)
            except:
                formula = Formula(item)
                MassListHelper.addMassTo(
                    masslist, MassListItem(formula.mass(), [formula]), rtol)

        self.showMasslist()

    @state_node
    def rmMass(self):
        indexes = get_tablewidget_selected_row(self.ui.tableWidget)
        masslist = self.info.masslist
        for index in reversed(indexes):
            masslist.pop(index)
        self.showMasslist()

    @state_node(withArgs=True)
    def group_plus(self, times: float):
        abs_times = abs(times)
        sign = times / abs_times
        group = Formula(self.ui.groupLineEdit.text())
        group *= abs_times
        mass_delta = sign * group.mass()
        for item in self.info.masslist:
            if len(item.formulas) > 0:
                for f in item.formulas:
                    if sign > 0:
                        f += group
                    else:
                        f -= group
                if len(item.formulas) == 1:
                    item.position = item.formulas[0].mass()
                else:
                    item.position += mass_delta
            else:
                item.position += mass_delta
        self.showMasslist()

    def get_selected_index(self):
        return get_tablewidget_selected_row(self.ui.tableWidget)

    def read_masslist_from(self, f):
        rtol = self.info.rtol
        ret = []
        with open(f, "r") as file:
            reader = csv.reader(file)
            it = iter(reader)
            next(it)
            for row in it:
                position = row[0]
                formulas = row[1]
                formulas = [Formula(f)
                            for formula in formulas.split('/') if (f := formula.strip())]
                item = MassListItem(position, formulas)
                MassListHelper.addMassTo(ret, item, rtol)
        return ret

    @state_node
    def merge(self):
        ret, f = openfile("select mass list to merge", "CSV file(*.csv)")
        if not ret:
            return

        rtol = self.info.rtol
        masslist = self.info.masslist

        def func():
            imported = self.read_masslist_from(f)
            MassListHelper.mergeInto(masslist, imported, rtol)

        yield func
        self.showMasslist()

    @state_node
    def import_masslist(self):
        ret, f = openfile("select mass list to import", "CSV file(*.csv)")
        if not ret:
            return

        self.info.masslist = yield partial(self.read_masslist_from, f), "read mass list"
        self.showMasslist()

    @state_node
    def export(self):
        ret, f = savefile("save mass list", "CSV file(*.csv)", "masslist.csv")
        if not ret:
            return

        masslist = self.info.masslist
        export_split = self.ui.splitFormulaCheckBox.isChecked()

        def func():
            if export_split:
                dicts = [item.formulas[0].to_dict() if len(
                    item.formulas) == 1 else {} for item in masslist]
                # use dict instead of orderedset
                header = dict.fromkeys(["e", "C", "H", "O", "N"])
                for d in dicts:
                    header.update(d)
            with open(f, 'w', newline='') as file:
                writer = csv.writer(file)
                if export_split:
                    writer.writerow(['position', 'formulas', *header])
                    for item, d in zip(masslist, dicts):
                        writer.writerow([
                            item.position,
                            '/'.join(str(formula)
                                     for formula in item.formulas),
                            *(d.get(k, 0) for k in header)])
                else:
                    writer.writerow(['position', 'formulas'])
                    for item in masslist:
                        writer.writerow(
                            [item.position, '/'.join(str(formula) for formula in item.formulas)])

        yield func, "export mass list"
