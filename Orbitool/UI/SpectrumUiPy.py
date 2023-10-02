import csv
from typing import Union, Optional
from . import SpectrumUi
from PyQt6 import QtWidgets, QtCore
from .manager import state_node, Manager
from .utils import savefile

from ..models.spectrum.spectrum import Spectrum


class Widget(QtWidgets.QWidget):
    def __init__(self, manager: Manager, parent: Optional['QWidget'] = None) -> None:
        super().__init__()
        self.ui = SpectrumUi.Ui_Form()
        self.setupUi()
        self.manager = manager
        manager.init_or_restored.connect(self.restore)

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)

        self.ui.pushButton.clicked.connect(self.export)

    @property
    def info(self):
        return self.manager.workspace.info.spectrum_docker

    def restore(self):
        self.show_spectrum(self.info.spectrum)

    def show_spectrum(self, spectrum: Union[Spectrum, None]):
        self.info.spectrum = spectrum
        if not spectrum:
            return
        tableWidget = self.ui.tableWidget
        tableWidget.setRowCount(0)
        mass = spectrum.mz
        intensity = spectrum.intensity
        tableWidget.setRowCount(len(mass))
        for i, (m_row, i_row) in enumerate(zip(mass, intensity)):
            for j, v in enumerate((m_row, i_row)):
                item = QtWidgets.QTableWidgetItem(
                    format(v, '.6f') if v > 1e-6 else '0.0')
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
                tableWidget.setItem(i, j, item)

    @state_node
    def export(self):
        spectrum = self.info.spectrum
        if not spectrum:
            return
        ret, file = savefile("save as csv file", "CSV file(*.csv)")
        if not ret:
            return
        def func():
            with open(file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['mz', 'intensity'])
                writer.writerows(zip(spectrum.mz, spectrum.intensity))
        yield func
        

