from typing import Union, Optional, List
from datetime import datetime
from PyQt5 import QtWidgets, QtCore

from . import SpectraListUi
from .utils import showInfo, set_header_sizes
from . import utils
from .manager import BaseWidget, state_node

from .. import config

from ..structures.file import SpectrumInfo


class Widget(QtWidgets.QWidget, SpectraListUi.Ui_Form, BaseWidget):
    def __init__(self, widget_root: BaseWidget, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)

        self.comboBox.currentIndexChanged.connect(self.comboBox_changed)
        self.comboBox_position = []
        self.former_index = -1

        self.widget_root = widget_root
        self.tableWidget.itemSelectionChanged.connect(self.selection_changed)

    def setupUi(self, Form):
        super().setupUi(Form)

        set_header_sizes(self.tableWidget.horizontalHeader(), [210, 210])

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
        spectrum_infos: List[SpectrumInfo] = self.spectra_list.file_spectrum_info_list
        spectrum_infos = [
            info for info in spectrum_infos if info.average_index == 0]
        tableWidget.setRowCount(len(spectrum_infos))

        for i, info in enumerate(spectrum_infos):
            time_range = (info.start_time.strftime(config.timeFormat),
                          info.end_time.strftime(config.timeFormat))
            for j, v in enumerate(time_range):
                tableWidget.setItem(i, j, QtWidgets.QTableWidgetItem(v))

    def show_combobox_selection(self):
        spectra_list = self.spectra_list
        comboBox = self.comboBox
        if len(spectra_list.file_spectrum_info_list) > 0:
            if comboBox.count() == 0:
                self.comboBox_position.append(0)
                comboBox.addItem("File tab")

    @state_node(mode='e')
    def selection_changed(self):
        indexes = utils.get_tablewidget_selected_row(self.tableWidget)
        index = (0 if config.default_select else None) if len(
            indexes) == 0 else indexes[0]
        if index is None:
            self.spectra_list.selected_start_time = None
        else:
            item = self.tableWidget.item(index, 0)
            self.spectra_list.selected_start_time = datetime.strptime(
                item.text(), config.timeFormat)
