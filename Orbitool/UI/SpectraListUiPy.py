import csv
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional, Union
import os

from PyQt5 import QtCore, QtWidgets

from .. import setting
from ..structures.file import FileSpectrumInfo
from . import SpectraListUi, utils
from .manager import Manager, state_node
from .utils import openfolder, set_header_sizes, showInfo, get_tablewidget_selected_row

FILE_TAB = 0
CALIBRATE_TAB = 1


class Widget(QtWidgets.QWidget):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        ui = self.ui = SpectraListUi.Ui_Form()
        self.setupUi()

        manager.getters.spectra_list_selected_index.connect(
            self.get_selected_index)
        manager.init_or_restored.connect(self.restore)

        ui.comboBox.currentIndexChanged.connect(self.comboBox_changed)
        self.comboBox_position = {}
        self.former_index = -1

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)

        set_header_sizes(ui.tableWidget.horizontalHeader(), [210, 210])
        self.show_combobox_selection()
        ui.exportSelectPushButton.clicked.connect(
            lambda: self.export("select"))
        ui.exportAllPushButton.clicked.connect(lambda: self.export("all"))

    def restore(self):
        ui = self.ui
        ui.comboBox.currentIndexChanged.disconnect(self.comboBox_changed)
        self.spectra_list.ui_state.set_state(ui)
        self.former_index = -1
        self._comboBox_changed()
        ui.comboBox.currentIndexChanged.connect(self.comboBox_changed)

    def updateState(self):
        self.spectra_list.ui_state.fromComponents(self.ui, [
            self.ui.comboBox])

    @state_node(mode='e')
    def comboBox_changed(self):
        self._comboBox_changed()

    def _comboBox_changed(self):
        ui = self.ui
        current = ui.comboBox.currentData()
        if self.former_index == current:
            return
        if self.former_index != -1:
            self.comboBox_position[self.former_index] = ui.tableWidget.verticalScrollBar(
            ).sliderPosition()
        ui.tableWidget.setRowCount(0)
        if current == FILE_TAB:
            self.show_file_infos()
        elif current == CALIBRATE_TAB:
            self.show_calibration_infos()

        ui.tableWidget.verticalScrollBar().setSliderPosition(
            self.comboBox_position.get(current, 0))
        self.former_index = current

    @property
    def spectra_list(self):
        return self.manager.workspace.spectra_list

    def show_file_infos(self):
        tableWidget = self.ui.tableWidget
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

        for i, (info, end) in enumerate(zip(infos, ends)):
            time_range = (setting.format_time(info.start_time),
                          setting.format_time(end))
            for j, v in enumerate(time_range):
                tableWidget.setItem(i, j, QtWidgets.QTableWidgetItem(v))

    def show_calibration_infos(self):
        tableWidget = self.ui.tableWidget
        infos = self.manager.workspace.calibration_tab.info.calibrated_spectrum_infos
        self.spectra_list.info.shown_indexes = list(range(len(infos)))
        tableWidget.setRowCount(len(infos))
        for i, info in enumerate(infos):
            tableWidget.setItem(i, 0, QtWidgets.QTableWidgetItem(
                setting.format_time(info.start_time)))
            tableWidget.setItem(i, 1, QtWidgets.QTableWidgetItem(
                setting.format_time(info.end_time)))

    def show_combobox_selection(self):
        comboBox = self.ui.comboBox
        comboBox.clear()
        comboBox.addItem("File tab", FILE_TAB)
        comboBox.addItem("Calibrate tab", CALIBRATE_TAB)

    def get_selected_index(self):
        indexes = utils.get_tablewidget_selected_row(self.ui.tableWidget)
        if len(indexes) == 0:
            if setting.general.default_select:
                return 0
            raise ValueError("Please select a spectrum in spectra list")
        return indexes[0]

    @state_node(withArgs=True)
    def export(self, mode: Literal["select", "all"]):
        ret, folder = openfolder("choose a folder to place spectra")

        if not ret:
            return

        folder = Path(folder)
        for _ in folder.glob("*"):
            folder = folder / \
                f"exported-spectra-{setting.format_export_time(datetime.now())}"
            folder.mkdir(parents=True)
            break

        comboxBox = self.ui.comboBox
        data = comboxBox.currentData()

        manager = self.manager
        if data == FILE_TAB:
            spectra = self.manager.workspace.noise_tab.raw_spectra
        elif data == CALIBRATE_TAB:
            spectra = self.manager.workspace.calibration_tab.calibrated_spectra

        rows = get_tablewidget_selected_row(self.ui.tableWidget)

        if mode == "select":
            def iter_select():
                for row in rows:
                    yield spectra[row]
            iterator = iter_select()
        else:
            iterator = spectra

        def func():
            for spectrum in manager.tqdm(iterator):
                filename = f"spectrum {setting.format_export_time(spectrum.start_time)}-{setting.format_export_time(spectrum.end_time)}"
                manager.msg.emit(f"export {filename}")
                with open(folder / f"{filename}.csv", 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['mz', 'intensity'])
                    writer.writerows(zip(spectrum.mz, spectrum.intensity))
            os.startfile(folder)
        yield func
