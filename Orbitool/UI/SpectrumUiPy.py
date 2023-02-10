import csv
from typing import Union, Optional
from . import SpectrumUi
from PyQt5 import QtWidgets, QtCore
from .manager import state_node, Manager
from .utils import savefile

from ..structures.spectrum import Spectrum


class Widget(QtWidgets.QWidget, SpectrumUi.Ui_Form):
    def __init__(self, manager: Manager, parent: Optional['QWidget'] = None) -> None:
        super().__init__()
        self.setupUi(self)
        self.manager = manager
        manager.init_or_restored.connect(self.restore)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.pushButton.clicked.connect(self.export)

    @property
    def info(self):
        return self.manager.workspace.spectrum_docker.info

    def restore(self):
        self.show_spectrum(self.info.spectrum)

    def show_spectrum(self, spectrum: Union[Spectrum, None]):
        self.info.spectrum = spectrum
        if not spectrum:
            return
        tableWidget = self.tableWidget
        tableWidget.setRowCount(0)
        mass = spectrum.mz
        intensity = spectrum.intensity
        tableWidget.setRowCount(len(mass))
        for i, (m_row, i_row) in enumerate(zip(mass, intensity)):
            for j, v in enumerate((m_row, i_row)):
                item = QtWidgets.QTableWidgetItem(
                    format(v, '.6f') if v > 1e-6 else '0.0')
                item.setTextAlignment(QtCore.Qt.AlignRight)
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
        

