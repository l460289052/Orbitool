from datetime import datetime
from typing import Dict, get_args
from PyQt5 import QtCore, QtWidgets
from .TimeseriesTabUi import Ui_Form
from Orbitool.config import _Setting
from Orbitool.utils.time_format import converters
from .common import BaseTab


class Tab(BaseTab):
    def __init__(self, parent: QtWidgets.QWidget, setting: _Setting) -> None:
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        self.init(setting)

    def init(self, setting: _Setting):
        ui = self.ui

        timeseries = setting.timeseries

        ui.mzRangeTargetComboBox.addItems(get_args(timeseries.__fields__["mz_sum_target"].type_))
        ui.mzRangeTargetComboBox.setCurrentText(timeseries.mz_sum_target)
        ui.mzRangePeakfitFuncCommboBox.addItems(get_args(timeseries.__fields__["mz_sum_func"].type_))
        ui.mzRangePeakfitFuncCommboBox.setCurrentText(timeseries.mz_sum_func)


        now = datetime.now().replace(microsecond=0)
        self.checkboxes:Dict[str, QtWidgets.QCheckBox] = {}
        for name, (converter, _) in converters.items():
            cb = QtWidgets.QCheckBox(
                f"{name}, example: {converter(now)}")
            cb.setChecked(name in timeseries.export_time_formats)
            self.checkboxes[name] = cb
            ui.timeformatVerticalLayout.addWidget(cb)


    def stash_setting(self, setting: _Setting):
        ui = self.ui
        timeseries = setting.timeseries

        timeseries.mz_sum_target = ui.mzRangeTargetComboBox.currentText()
        timeseries.mz_sum_func = ui.mzRangePeakfitFuncCommboBox.currentText()

        formats = set()
        for name, cb in self.checkboxes.items():
            if cb.isChecked():
                formats.add(name)
        timeseries.export_time_formats = formats

        
