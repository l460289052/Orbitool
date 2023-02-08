import contextlib
from copy import copy
import enum
from functools import partial
from typing import List, Union, Optional
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
        self.sbs: List[Union[QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox]] = [
            self.mzMinDoubleSpinBox, self.mzMaxDoubleSpinBox, self.chargeSpinBox,
            self.rtolDoubleSpinBox, self.globalLimitSpinBox, self.dbeMinDoubleSpinBox,
            self.dbeMaxDoubleSpinBox]
        self.cbs: List[QtWidgets.QCheckBox] = [
            self.nitrogenRuleCheckBox, self.dbeLimitCheckBox]

        def change_only_focus(self, e: QtGui.QWheelEvent):
            if self.hasFocus():
                return type(self).wheelEvent(self, e)
            else:
                e.ignore()

        for sb in self.sbs:
            sb.wheelEvent = partial(change_only_focus, sb)
            sb.valueChanged.connect(self.update_calc)

        for cb in self.cbs:
            cb.stateChanged.connect(self.update_calc)

        # self.elementAddToolButton.clicked.connect(self.restrictedAddElement)
        # self.isotopeAddToolButton.clicked.connect(self.restrictedAddIsotope)
        # self.isotopeDelToolButton.clicked.connect(self.restrictedDelIsotopes)

        # self.unrestrictedAddToolButton.clicked.connect(self.forceAdd)
        # self.unrestrictedDelToolButton.clicked.connect(self.forceDel)

        # self.applyPushButton.clicked.connect(self.applyChange)

        # self.calcPushButton.clicked.connect(lambda: self.calc(False))
        # self.forcePushButton.clicked.connect(lambda: self.calc(True))

    @contextlib.contextmanager
    def without_info_change(self):
        for sb in self.sbs:
            sb.valueChanged.disconnect(self.update_calc)
        for cb in self.cbs:
            cb.stateChanged.disconnect(self.update_calc)
        yield
        for sb in self.sbs:
            sb.valueChanged.connect(self.update_calc)
        for cb in self.cbs:
            cb.stateChanged.connect(self.update_calc)

    @property
    def formula(self):
        return self.manager.workspace.formula_docker

    def show_or_restore(self):
        self.show_info()
        self.show_isotopes()
        self.show_element_infos()

    def show_info(self):
        info = self.formula.info
        with self.without_info_change():
            self.mzMinDoubleSpinBox.setValue(info.mz_min)
            self.mzMaxDoubleSpinBox.setValue(info.mz_max)
            self.chargeSpinBox.setValue(info.charge)
            self.rtolDoubleSpinBox.setValue(info.calc_gen.rtol * 1e6)
            self.globalLimitSpinBox.setValue(info.calc_gen.global_limit)
            self.nitrogenRuleCheckBox.setChecked(info.calc_gen.nitrogen_rule)
            self.dbeLimitCheckBox.setChecked(info.calc_gen.dbe_limit)
            self.dbeMinDoubleSpinBox.setValue(info.calc_gen.DBEMin)
            self.dbeMinDoubleSpinBox.setMaximum(info.calc_gen.DBEMax)
            self.dbeMaxDoubleSpinBox.setValue(info.calc_gen.DBEMax)
            self.dbeMaxDoubleSpinBox.setMinimum(info.calc_gen.DBEMin)

    def show_isotopes(self):
        info = self.formula.info
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

    def show_element_infos(self):
        info = self.formula.info
        gen = info.calc_gen

        icon = self.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_DialogDiscardButton)
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

    @state_node
    def update_calc(self):
        info = self.formula.info
        info.mz_min = self.mzMinDoubleSpinBox.value()
        info.mz_max = self.mzMaxDoubleSpinBox.value()
        info.charge = self.chargeSpinBox.value()
        info.calc_gen.rtol = self.rtolDoubleSpinBox.value() * 1e-6
        info.calc_gen.global_limit = self.globalLimitSpinBox.value()
        info.calc_gen.nitrogen_rule = self.nitrogenRuleCheckBox.isChecked()
        info.calc_gen.dbe_limit = self.dbeLimitCheckBox.isChecked()
        info.calc_gen.DBEMin = self.dbeMinDoubleSpinBox.value()
        info.calc_gen.DBEMax = self.dbeMaxDoubleSpinBox.value()
        self.show_info()

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
