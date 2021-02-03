from typing import Union, Optional
from PyQt5 import QtWidgets, QtCore

from . import SpectraListUi
from .utils import showInfo, set_header_sizes
from . import utils
from .manager import BaseWidget, state_node

from Orbitool import config


class Widget(QtWidgets.QWidget, SpectraListUi.Ui_Form, BaseWidget):
    def __init__(self, widget_root: BaseWidget, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.widget_root = widget_root
        self.setupUi(self)

        set_header_sizes(self.tableWidget.horizontalHeader(), [130, 130])

        self.comboBox.currentIndexChanged.connect(self.comboBox_changed)
        self.comboBox_position = []
        self.former_index = -1

        self.tableWidget.itemSelectionChanged.connect(self.selection_changed)

    @state_node(withArgs=True, mode='x')
    def comboBox_changed(self, index):
        if self.former_index == index:
            return
        if self.former_index != -1:
            self.comboBox_position[self.former_index] = self.tableWidget.verticalScrollBar(
            ).sliderPosition()
        if index == 0:
            self.show_file_infos()

        self.tableWidget.verticalScrollBar().setSliderPosition(
            self.comboBox_position[index])

    @property
    def spectra_list(self):
        return self.current_workspace.spectra_list

    def show_file_infos(self):
        tableWidget = self.tableWidget
        tableWidget.setRowCount(0)
        spectrum_infos = self.spectra_list.file_spectrum_info_list
        tableWidget.setRowCount(len(spectrum_infos))

        for i, info in enumerate(spectrum_infos):
            time_range = (info.startTime.strftime(config.timeFormat),
                          info.endTime.strftime(config.timeFormat))
            for j, v in enumerate(time_range):
                tableWidget.setItem(i, j, QtWidgets.QTableWidgetItem(v))

    def show_combobox_selection(self):
        spectra_list = self.spectra_list
        comboBox = self.comboBox
        if len(spectra_list.file_spectrum_info_list) > 0:
            if comboBox.count() == 0:
                self.comboBox_position.append(0)
                comboBox.addItem("File tab")

    def selection_changed(self):
        indexes = utils.get_tablewidget_selected_row(self.tableWidget)
        self.current_workspace.selected_spectrum_index = None if len(
            indexes) == 0 else indexes[0]
