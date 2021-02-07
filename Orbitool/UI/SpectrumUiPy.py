from typing import Union, Optional
from . import SpectrumUi
from PyQt5 import QtWidgets, QtCore
from .manager import state_node, BaseWidget

from Orbitool.structures.spectrum import Spectrum


class Widget(QtWidgets.QWidget, SpectrumUi.Ui_Form, BaseWidget):
    def __init__(self, widget_root, parent: Optional['QWidget'] = None) -> None:
        super().__init__()
        self.setupUi(self)
        self.widget_root = widget_root

    def show_spectrum(self, spectrum: Spectrum):
        tableWidget = self.tableWidget
        tableWidget.setRowCount(0)
        mass = spectrum.mass
        intensity = spectrum.intensity
        tableWidget.setRowCount(len(mass))
        for i, (m_row, i_row) in enumerate(zip(mass, intensity)):
            for j, v in enumerate((m_row, i_row)):
                item = QtWidgets.QTableWidgetItem(format(v,'.6f') if v>1e-6 else '0.0')
                item.setTextAlignment(QtCore.Qt.AlignRight)
                tableWidget.setItem(i, j, item)
