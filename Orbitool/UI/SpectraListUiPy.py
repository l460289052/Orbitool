import csv
from datetime import datetime
from typing import List, Optional, Union
import os

from PyQt5 import QtCore, QtWidgets

from .. import get_config
from ..structures.file import FileSpectrumInfo
from . import SpectraListUi, utils
from .manager import Manager, state_node
from .utils import openfolder, set_header_sizes, showInfo

FILE_TAB = 0
CALIBRATE_TAB = 1


class Widget(QtWidgets.QWidget, SpectraListUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)

        manager.getters.spectra_list_selected_index.connect(
            self.get_selected_index)
        manager.init_or_restored.connect(self.restore)

        self.comboBox.currentIndexChanged.connect(self.comboBox_changed)
        self.comboBox_position = {}
        self.former_index = -1

    def setupUi(self, Form):
        super().setupUi(Form)

        set_header_sizes(self.tableWidget.horizontalHeader(), [210, 210])
        self.show_combobox_selection()
        self.exportPushButton.clicked.connect(self.export)

    def restore(self):
        self.comboBox.currentIndexChanged.disconnect(self.comboBox_changed)
        self.spectra_list.ui_state.set_state(self)
        self._comboBox_changed()
        self.comboBox.currentIndexChanged.connect(self.comboBox_changed)
        # TODO: restore 无效

    def updateState(self):
        self.spectra_list.ui_state.fromComponents(self, [
            self.comboBox])

    @state_node(mode='x')
    def comboBox_changed(self):
        self._comboBox_changed()

    def _comboBox_changed(self):
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

    @property
    def spectra_list(self):
        return self.manager.workspace.spectra_list

    def show_file_infos(self):
        tableWidget = self.tableWidget
        spectrum_infos: List[FileSpectrumInfo] = self.manager.workspace.file_tab.info.spectrum_infos

        shown_indexes: List[int] = []
        infos: List[FileSpectrumInfo] = []
        ends: List[datetime] = []
        for index, info in enumerate(spectrum_infos):
            if info.average_index == 0:
                shown_indexes.append(index)
                infos.append(info)
                ends.append(info.end_time)
            else:
                ends[-1] = info.end_time
        self.spectra_list.info.shown_indexes = shown_indexes
        tableWidget.setRowCount(len(infos))

        config = get_config()

        for i, (info, end) in enumerate(zip(infos, ends)):
            time_range = (info.start_time.strftime(config.format_time),
                          end.strftime(config.format_time))
            for j, v in enumerate(time_range):
                tableWidget.setItem(i, j, QtWidgets.QTableWidgetItem(v))

    def show_calibration_infos(self):
        tableWidget = self.tableWidget
        infos = self.manager.workspace.calibration_tab.info.calibrated_spectrum_infos
        self.spectra_list.info.shown_indexes = list(range(len(infos)))
        tableWidget.setRowCount(len(infos))
        config = get_config()
        for i, info in enumerate(infos):
            tableWidget.setItem(i, 0, QtWidgets.QTableWidgetItem(
                info.start_time.strftime(config.format_time)))
            tableWidget.setItem(i, 1, QtWidgets.QTableWidgetItem(
                info.end_time.strftime(config.format_time)))

    def show_combobox_selection(self):
        comboBox = self.comboBox
        comboBox.clear()
        comboBox.addItem("File tab", FILE_TAB)
        comboBox.addItem("Calibrate tab", CALIBRATE_TAB)

    def get_selected_index(self):
        indexes = utils.get_tablewidget_selected_row(self.tableWidget)
        if len(indexes) == 0:
            if get_config().default_select:
                return 0
            raise ValueError("Please select a spectrum in spectra list")
        return indexes[0]

    @state_node
    def export(self):
        ret, folder = openfolder("choose a folder to place spectra")

        if not ret:
            return

        comboxBox = self.comboBox
        data = comboxBox.currentData()

        manager = self.manager
        if data == FILE_TAB:
            spectra = self.manager.workspace.noise_tab.raw_spectra
        elif data == CALIBRATE_TAB:
            spectra = self.manager.workspace.calibration_tab.calibrated_spectra

        def func():
            config = get_config()
            for spectrum in manager.tqdm(spectra):
                filename = f"spectrum {spectrum.start_time.strftime(config.format_export_time)}-{spectrum.end_time.strftime(config.format_export_time)}"
                manager.msg.emit(f"export {filename}")
                with open(os.path.join(folder, f"{filename}.csv"), 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['mz', 'intensity'])
                    writer.writerows(zip(spectrum.mz, spectrum.intensity))
        yield func
