from copy import copy
import enum
from functools import partial
from typing import Union, Optional
from . import FormulaUi

from PyQt5 import QtWidgets, QtCore, QtGui
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
        # FormulaUi.Ui_Form.setupUi(self, Form)
        super().setupUi(Form)

        def change_only_focus(self, e: QtGui.QWheelEvent):
            if self.hasFocus():
                return type(self).wheelEvent(self, e)
            else:
                e.ignore()

        for sb in [
                self.chargeSpinBox,
                self.rtolDoubleSpinBox,
                self.globalLimitSpinBox,
                self.dbeMinDoubleSpinBox,
                self.dbeMaxDoubleSpinBox]:
            sb.wheelEvent = partial(change_only_focus, sb)

        # self.elementAddToolButton.clicked.connect(self.restrictedAddElement)
        # self.isotopeAddToolButton.clicked.connect(self.restrictedAddIsotope)
        # self.isotopeDelToolButton.clicked.connect(self.restrictedDelIsotopes)

        # self.unrestrictedAddToolButton.clicked.connect(self.forceAdd)
        # self.unrestrictedDelToolButton.clicked.connect(self.forceDel)

        # self.applyPushButton.clicked.connect(self.applyChange)

        # self.calcPushButton.clicked.connect(lambda: self.calc(False))
        # self.forcePushButton.clicked.connect(lambda: self.calc(True))

    @property
    def formula(self):
        return self.manager.workspace.formula_docker

    def show_or_restore(self):
        info = self.formula.info
        self.chargeSpinBox.setValue(info.charge)
        self.rtolDoubleSpinBox.setValue(info.calc_gen.rtol * 1e6)
        self.globalLimitSpinBox.setValue(info.calc_gen.global_limit)
        self.nitrogenRuleCheckBox.setChecked(info.calc_gen.nitrogen_rule)
        self.dbeLimitCheckBox.setChecked(info.calc_gen.dbe_limit)
        self.dbeMinDoubleSpinBox.setValue(info.calc_gen.DBEMin)
        self.dbeMaxDoubleSpinBox.setValue(info.calc_gen.DBEMax)

        # show isotopes
        gen = info.calc_gen
        tree: QtWidgets.QTreeWidget = self.isotopeTreeWidget
        tree.clear()
        icon = self.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_DialogDiscardButton)
        pixmap = icon.pixmap(20, 20)

        def label(num: int):
            return QtWidgets.QLabel(str(num))

        def icon_label():
            label = QtWidgets.QLabel()
            label.setPixmap(pixmap)
            return label
        for e, e_num in gen.get_E_iter():
            e_item = QtWidgets.QTreeWidgetItem([e])
            custom_e = f"{e}[{e_num.e_num}]"
            custom = custom_e in gen.isotope_usable
            tree.addTopLevelItem(e_item)
            tree.setItemWidget(e_item, 1, icon_label())
            tree.setItemWidget(e_item, 2, label(e_num.min))
            tree.setItemWidget(e_item, 3, label(e_num.max))
            tree.setItemWidget(e_item, 4, factory.CheckBox(
                custom, f"{custom_e} custom", True, QtCore.Qt.LayoutDirection.RightToLeft))

            for i, i_num in sorted(gen.get_I_iter(e_num.e_num), key=lambda i: i[1].i_num != e_num.e_num):
                i_item = QtWidgets.QTreeWidgetItem([i])
                e_item.addChild(i_item)
                tree.setItemWidget(i_item, 1, icon_label())
                tree.setItemWidget(i_item, 2, label(i_num.min))
                tree.setItemWidget(i_item, 3, label(i_num.max))
                tree.setItemWidget(i_item, 4, factory.CheckBox(
                    i_num.global_limit, "global limit", True, QtCore.Qt.LayoutDirection.RightToLeft))
            tree.setExpanded(tree.indexFromItem(e_item), True)
        for i in range(tree.columnCount()):
            tree.resizeColumnToContents(i)

        # show element infos
        table: QtWidgets.QTableWidget = self.elementTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(gen.element_states))

        def f2text4(val: float):
            item = QtWidgets.QTableWidgetItem(format(val, '.4f'))
            item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            return item

        def f2text1(val: float):
            item = QtWidgets.QTableWidgetItem(format(val, '.1f'))
            item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            return item

        def del_icon():
            return QtWidgets.QTableWidgetItem(icon, "")
        for row, (e, e_info) in enumerate(gen.element_states.items()):
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(e))
            if e.startswith("e"):
                f = Formula(charge=-1)
            else:
                f = Formula(e)
            table.setItem(row, 1, f2text4(f.mass()))
            table.setItem(row, 2, del_icon())
            for col, val in enumerate(e_info.to_list(), 3):
                table.setItem(row, col, f2text1(val))
        table.resizeColumnsToContents()

    @state_node(withArgs=True)
    def calc(self, force: bool):
        manager = self.manager
        with manager.not_check():
            self.applyChange()

        text = self.inputLineEdit.text()

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
        table.setCellWidget(row, 1, factory.CheckBox(False))
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
