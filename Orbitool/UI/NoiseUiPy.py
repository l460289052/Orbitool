from typing import Union, Optional
from PyQt5 import QtWidgets, QtCore

from . import NoiseUi
from . import utils
from .manager import BaseWidget, state_node, Thread

from Orbitool.structures.file import SpectrumInfo


class Widget(QtWidgets.QWidget, NoiseUi.Ui_Form, BaseWidget):
    selected_spectrum_average = QtCore.pyqtSignal()

    def __init__(self, widget_root, parent: Optional['QWidget'] = None) -> None:
        super().__init__()
        self.setupUi(self)
        self.widget_root = widget_root

        self.toolBox.setCurrentIndex(0)
        self.showAveragePushButton.clicked.connect(self.showSelectedSpectrum)

    @property
    def noise(self):
        return self.current_workspace.noise_tab

    @state_node
    def showSelectedSpectrum(self):
        workspace = self.current_workspace
        index = workspace.spectra_list.selected_spectrum_index
        spectrum_info: SpectrumInfo = workspace.spectra_list.file_spectrum_info_list[index]
        return Thread(spectrum_info.get_spectrum, (workspace.noise_tab.current_spectrum, ))

    @showSelectedSpectrum.thread_node
    def showSelectedSpectrum(self, result, args):
        self.selected_spectrum_average.emit()
        # plot
