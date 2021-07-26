import csv
from typing import Optional, Union
from functools import partial

from PyQt5 import QtCore, QtWidgets

from ..functions.peakfit import masslist as masslist_func
from ..structures.spectrum import MassListItem
from ..utils.formula import Formula
from . import MassListUi
from .manager import Manager, state_node
from .utils import get_tablewidget_selected_row, openfile, savefile


class Widget(QtWidgets.QWidget, MassListUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        self.manager.register_func("mass list select", self.get_selected_index)
        self.manager.inited_or_restored.connect(self.restore)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.addPushButton.clicked.connect(self.addMass)
        self.removePushButton.clicked.connect(self.rmMass)

        self.groupPlusPushButton.clicked.connect(lambda: self.group_plus(1))
        self.groupMinusPushButton.clicked.connect(lambda: self.group_plus(-1))

        self.mergePushButton.clicked.connect(self.merge)
        self.importPushButton.clicked.connect(self.import_masslist)
        self.exportPushButton.clicked.connect(self.export)

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
        text = self.addItemLineEdit.text()
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

    @state_node(withArgs=True)
    def group_plus(self, times):
        abs_times = abs(times)
        sign = times / abs_times
        group = Formula(self.groupLineEdit.text())
        group *= abs_times
        mass_delta = sign * group.mass()
        for item in self.masslist.masslist:
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
        return get_tablewidget_selected_row(self.tableWidget)

    def read_masslist_from(self, f):
        rtol = self.masslist.rtol
        ret = []
        with open(f, "r") as file:
            reader = csv.reader(file)
            it = iter(reader)
            next(it)
            for row in it:
                position = row[0]
                formulas = row[1]
                formulas = [Formula(formula)
                            for formula in formulas.split('/')]
                item = MassListItem(position=position, formulas=formulas)
                masslist_func.addMassTo(ret, item, rtol)
        return ret

    @state_node
    def merge(self):
        ret, f = openfile("select mass list to merge", "CSV file(*.csv)")
        if not ret:
            return

        rtol = self.masslist.rtol
        masslist = self.masslist.masslist

        def func():
            imported = self.read_masslist_from(f)
            masslist_func.MergeInto(masslist, imported, rtol)

        yield func
        self.showMasslist()

    @state_node
    def import_masslist(self):
        ret, f = openfile("select mass list to import", "CSV file(*.csv)")
        if not ret:
            return

        self.masslist.masslist = yield partial(self.read_masslist_from, f), "read mass list"
        self.showMasslist()

    @state_node
    def export(self):
        ret, f = savefile("save mass list", "CSV file(*.csv)", "masslist.csv")
        if not ret:
            return

        masslist = self.masslist.masslist
        export_split = self.splitFormulaCheckBox.isChecked()

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
