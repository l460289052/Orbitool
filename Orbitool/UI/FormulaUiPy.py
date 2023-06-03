import contextlib
from copy import copy
import enum
from functools import partial
from typing import Callable, List, Union, Optional

from PyQt5 import QtWidgets, QtCore, QtGui
from itertools import chain
from .manager import Manager, state_node
from .component import factory
from ..utils.formula import Formula, parse_element, ElementState
from .utils import get_tablewidget_selected_row, showInfo
from . import FormulaResultUiPy

from . import FormulaUi

class Widget(QtWidgets.QWidget):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.ui = FormulaUi.Ui_Form()

        self.setupUi()
        self.manager.init_or_restored.connect(self.show_or_restore)

    def setupUi(self):
        self.ui.setupUi(self)
        ui = self.ui


        self.sbs: List[Union[QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox]] = [
            ui.mzMinDoubleSpinBox, ui.mzMaxDoubleSpinBox, ui.chargeSpinBox,
            ui.rtolDoubleSpinBox, ui.globalLimitSpinBox, ui.dbeMinDoubleSpinBox,
            ui.dbeMaxDoubleSpinBox]
        self.cbs: List[QtWidgets.QCheckBox] = [
            ui.nitrogenRuleCheckBox, ui.dbeLimitCheckBox]

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

        ui.isotopeTreeWidget.itemClicked.connect(self.isotope_item_clicked)
        ui.isotopeAddToolButton.clicked.connect(self.isotope_add)

        ui.elementShowPushButton.clicked.connect(self.show_element_infos)
        ui.elementHidePushButton.clicked.connect(lambda a: self.hide_element_infos())

        ui.elementTableWidget.itemClicked.connect(self.element_item_clicked)
        ui.elementAddToolButton.clicked.connect(self.element_add)

        ui.calcPushButton.clicked.connect(self.calc)

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
    def info(self):
        return self.manager.workspace.info.formula_docker

    def show_or_restore(self):
        self.show_info()
        self.show_isotopes()
        self.hide_element_infos()

    def show_info(self):
        info = self.info
        ui = self.ui
        with self.without_info_change():
            ui.mzMinDoubleSpinBox.setValue(info.mz_min)
            ui.mzMaxDoubleSpinBox.setValue(info.mz_max)
            ui.chargeSpinBox.setValue(info.charge)
            ui.rtolDoubleSpinBox.setValue(info.calc_gen.rtol * 1e6)
            ui.globalLimitSpinBox.setValue(info.calc_gen.global_limit)
            ui.nitrogenRuleCheckBox.setChecked(info.calc_gen.nitrogen_rule)
            ui.dbeLimitCheckBox.setChecked(info.calc_gen.dbe_limit)
            ui.dbeMinDoubleSpinBox.setValue(info.calc_gen.DBEMin)
            ui.dbeMinDoubleSpinBox.setMaximum(info.calc_gen.DBEMax)
            ui.dbeMaxDoubleSpinBox.setValue(info.calc_gen.DBEMax)
            ui.dbeMaxDoubleSpinBox.setMinimum(info.calc_gen.DBEMin)

    def show_isotopes(self):
        info = self.info
        gen = info.calc_gen
        tree: QtWidgets.QTreeWidget = self.ui.isotopeTreeWidget
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

        def check_box(text, checked: bool, key: str, func: Callable):
            cb = QtWidgets.QCheckBox(text)
            cb.setChecked(checked)
            cb.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
            cb.stateChanged.connect(lambda e: func(key, e))
            return cb

        def custom_func(key: str, e: int):
            if e == QtCore.Qt.CheckState.Checked:
                gen.add_EI(key)
            elif e == QtCore.Qt.CheckState.Unchecked:
                gen.del_EI(key)
            self.show_isotopes()

        def global_limit_func(key: str, e: int):
            if e == QtCore.Qt.CheckState.Checked:
                gen.isotope_usable[key].global_limit = True
            elif e == QtCore.Qt.CheckState.Unchecked:
                gen.isotope_usable[key].global_limit = False
            self.show_isotopes()

        for e, e_num in gen.get_E_iter():
            e_item = QtWidgets.QTreeWidgetItem([e])
            custom_e = f"{e}[{e_num.e_num}]"
            custom = custom_e in gen.isotope_usable
            tree.addTopLevelItem(e_item)
            tree.setItemWidget(e_item, 1, icon_label())
            tree.setItemWidget(e_item, 2, label(e_num.min))
            tree.setItemWidget(e_item, 3, label(e_num.max))
            tree.setItemWidget(e_item, 4, check_box(
                f"{custom_e} custom", custom, custom_e, custom_func))

            for i, i_num in sorted(gen.get_I_iter(e_num.e_num), key=lambda i: i[1].i_num != e_num.e_num):
                i_item = QtWidgets.QTreeWidgetItem([i])
                e_item.addChild(i_item)
                tree.setItemWidget(i_item, 1, icon_label())
                tree.setItemWidget(i_item, 2, label(i_num.min))
                tree.setItemWidget(i_item, 3, label(i_num.max))
                tree.setItemWidget(i_item, 4, check_box(
                    "global limit", i_num.global_limit, i, global_limit_func))
            tree.setExpanded(tree.indexFromItem(e_item), True)
        for i in range(tree.columnCount()):
            tree.resizeColumnToContents(i)
    
    @state_node(withArgs=True, mode="a")
    def hide_element_infos(self, a:bool=True):
        b = not a
        ui = self.ui
        ui.elementHidePushButton.setVisible(b)
        ui.elementTableWidget.setVisible(b)
        ui.elementLineEdit.setVisible(b)
        ui.elementAddToolButton.setVisible(b)
        

    @state_node(mode="a")
    def show_element_infos(self):
        self.hide_element_infos(False)
        ui = self.ui
        info = self.info
        gen = info.calc_gen

        icon = self.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_DialogDiscardButton)
        table: QtWidgets.QTableWidget = ui.elementTableWidget
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

    @state_node(mode="a")
    def update_calc(self):
        info = self.info
        ui = self.ui
        info.mz_min = ui.mzMinDoubleSpinBox.value()
        info.mz_max = ui.mzMaxDoubleSpinBox.value()
        info.charge = ui.chargeSpinBox.value()
        info.calc_gen.rtol = ui.rtolDoubleSpinBox.value() * 1e-6
        info.calc_gen.global_limit = ui.globalLimitSpinBox.value()
        info.calc_gen.nitrogen_rule = ui.nitrogenRuleCheckBox.isChecked()
        info.calc_gen.dbe_limit = ui.dbeLimitCheckBox.isChecked()
        info.calc_gen.DBEMin = ui.dbeMinDoubleSpinBox.value()
        info.calc_gen.DBEMax = ui.dbeMaxDoubleSpinBox.value()
        self.show_info()

    @state_node(withArgs=True, mode="a")
    def isotope_item_clicked(self, item: QtWidgets.QTreeWidgetItem, col: int):
        tree: QtWidgets.QTreeWidget = self.ui.isotopeTreeWidget
        gen = self.info.calc_gen
        key = item.text(0)
        i_num = gen.isotope_usable[key]
        if col == 1:  # del
            btn = QtWidgets.QToolButton()
            btn.setText("del")

            def del_iso():
                if i_num.i_num == 0:
                    if len(list(gen.get_I_iter(i_num.e_num))):
                        showInfo("Please remove the isotopes first")
                    else:
                        del gen.isotope_usable[key]
                else:
                    del gen.isotope_usable[key]
                btn.focusOutEvent = lambda e: None
                self.show_isotopes()
            btn.clicked.connect(del_iso)
            btn.focusOutEvent = lambda e: self.show_isotopes()
            tree.setItemWidget(item, col, btn)
            btn.setFocus()
        elif col == 2 or col == 3:  # min / max
            sb = QtWidgets.QSpinBox()
            if col == 2:
                values = (0, i_num.min, i_num.max)
            else:
                values = (i_num.min, i_num.max, gen.global_limit if i_num.global_limit else 999)
            sb.setMinimum(values[0])
            sb.setValue(values[1])
            sb.setMaximum(values[2])

            def focus_out(e):
                if col == 2:
                    i_num.min = sb.value()
                else:
                    i_num.max = sb.value()
                self.show_isotopes()
            sb.focusOutEvent = focus_out
            tree.setItemWidget(item, col, sb)
            sb.setFocus()

    @state_node
    def isotope_add(self):
        text: str = self.ui.isotopeLineEdit.text()
        try:
            gen = self.info.calc_gen
            gen.add_EI(text)
            f = Formula(text).findOrigin()
            assert str(f) in gen.element_states, f"Please add the element '{f}' infos first"
            self.show_isotopes()
            self.ui.isotopeLineEdit.setText("")
        except Exception as e:
            if text in gen.isotope_usable:
                del gen.isotope_usable[text]
            showInfo(str(e))

    @state_node(withArgs=True, mode="a")
    def element_item_clicked(self, item: QtWidgets.QTableWidgetItem):
        row = item.row()
        col = item.column()
        ele = self.info.calc_gen.element_states
        table: QtWidgets.QTableWidget = self.ui.elementTableWidget
        key = table.item(row, 0).text()
        if col == 2:  # del
            btn = QtWidgets.QToolButton()
            btn.setText("del")

            def del_ele():
                del ele[key]
                btn.focusOutEvent = lambda e: None
                self.show_element_infos()
            btn.clicked.connect(del_ele)
            btn.focusOutEvent = lambda e: self.show_element_infos()
            table.setItem(row, col, QtWidgets.QTableWidgetItem(""))
            table.setCellWidget(row, col, btn)
            btn.setFocus()
        elif 3<=col <=7:
            dsb = QtWidgets.QDoubleSpinBox()
            dsb.setDecimals(2)
            s = ele[key]
            if col == 3:
                values = (-99,s.DBE2,99)
            elif col == 4:
                values = (-99,s.HMin,s.HMax)
            elif col == 5:
                values = (s.HMin, s.HMax, 99)
            elif col == 6:
                values = (-99, s.OMin, s.OMax)
            elif col == 7:
                values = (s.OMin, s.OMax, 99)
            dsb.setMinimum(values[0])
            dsb.setValue(values[1])
            dsb.setMaximum(values[2])
            
            def focus_out(e):
                v = dsb.value()
                if col == 3:
                    s.DBE2 = v
                elif col == 4:
                    s.HMin = v
                elif col == 5:
                    s.HMax = v
                elif col == 6:
                    s.OMin = v
                elif col == 7:
                    s.OMax = v
                self.show_element_infos()
            dsb.focusOutEvent = focus_out
            table.setItem(row, col, QtWidgets.QTableWidgetItem(""))
            table.setCellWidget(row, col, dsb)
            table.resizeColumnsToContents()
            dsb.setFocus()

    @state_node
    def element_add(self):
        text: str = self.ui.elementLineEdit.text()
        try:
            e, i = parse_element(text)
            gen = self.info.calc_gen
            if e in gen.element_states:
                return
            gen.element_states[e] = ElementState()
            self.show_element_infos()
        except Exception as e:
            showInfo(str(e))

    @state_node
    def calc(self):
        manager = self.manager

        text = self.ui.inputLineEdit.text()

        if manager.formulas_result_win is not None:
            manager.formulas_result_win.close()
            del manager.formulas_result_win
        manager.formulas_result_win = FormulaResultUiPy.Window.FactoryCalc(
            manager, text)
        manager.formulas_result_win.show()
