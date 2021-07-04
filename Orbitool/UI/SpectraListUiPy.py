from typing import Union, Optional, List
from datetime import datetime
from PyQt5 import QtWidgets, QtCore

from . import SpectraListUi
from .utils import showInfo, set_header_sizes
from . import utils
from .manager import Manager, state_node

from .. import config

from ..structures.file import FileSpectrumInfo

FILE_TAB = 0
CALIBRATE_TAB = 1


class Widget(QtWidgets.QWidget, SpectraListUi.Ui_Form):
    def __init__(self, manager: Manager, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.manager = manager
        self.setupUi(self)

        self.comboBox.currentIndexChanged.connect(self.comboBox_changed)
        self.comboBox_position = {}
        self.former_index = -1

        self.tableWidget.itemSelectionChanged.connect(self.selection_changed)

    def setupUi(self, Form):
        super().setupUi(Form)

        set_header_sizes(self.tableWidget.horizontalHeader(), [210, 210])
        self.show_combobox_selection()

    @state_node(mode='x')
    def comboBox_changed(self):
        current = self.comboBox.currentData()
        if self.former_index == current:
            return
        if self.former_index != -1:
            self.comboBox_position[self.former_index] = self.tableWidget.verticalScrollBar(
            ).sliderPosition()
        self.tableWidget.setRowCount(0)
        if current == FILE_TAB:
            self.show_file_infos()
        elif current == CALIBRATE_TAB:
            self.show_calibration_infos()

        self.tableWidget.verticalScrollBar().setSliderPosition(
            self.comboBox_position.get(current, 0))
        self.former_index = current
        self.tableWidget.show()

    @property
    def spectra_list(self):
        return self.manager.workspace.spectra_list

    def show_file_infos(self):
        tableWidget = self.tableWidget
        spectrum_infos: List[FileSpectrumInfo] = self.manager.workspace.file_tab.info.spectrum_infos
        self.spectra_list.info.shown_indexes, spectrum_infos = zip(*[
            (index, info) for index, info in enumerate(spectrum_infos) if info.average_index == 0])
        tableWidget.setRowCount(len(spectrum_infos))

        for i, info in enumerate(spectrum_infos):
            time_range = (info.start_time.strftime(config.timeFormat),
                          info.end_time.strftime(config.timeFormat))
            for j, v in enumerate(time_range):
                tableWidget.setItem(i, j, QtWidgets.QTableWidgetItem(v))

    def show_calibration_infos(self):
        tableWidget = self.tableWidget
        infos = self.manager.workspace.calibration_tab.info.calibrated_spectrum_infos
        tableWidget.setRowCount(len(infos))
        for i, info in enumerate(infos):
            tableWidget.setItem(i, 0, QtWidgets.QTableWidgetItem(
                info.start_time.strftime(config.timeFormat)))
            tableWidget.setItem(i, 1, QtWidgets.QTableWidgetItem(
                info.end_time.strftime(config.timeFormat)))

    def show_combobox_selection(self):
        comboBox = self.comboBox
        comboBox.clear()
        comboBox.addItem("File tab", FILE_TAB)
        comboBox.addItem("Calibrate tab", CALIBRATE_TAB)

    @state_node(mode='e')
    def selection_changed(self):
        indexes = utils.get_tablewidget_selected_row(self.tableWidget)
        index = (0 if config.default_select else None) if len(
            indexes) == 0 else indexes[0]
        self.spectra_list.info.selected_index = self.spectra_list.info.shown_indexes[
            index]
