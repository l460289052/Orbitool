from typing import Union, Optional
from PyQt5 import QtWidgets, QtCore

from . import NoiseUi
from . import utils
from .manager import BaseWidget, state_node


class Widget(QtWidgets.QWidget, NoiseUi.Ui_Form, BaseWidget):
    def __init__(self, widget_root, parent: Optional['QWidget'] = None) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)
        self.widget_root = widget_root

        self.toolBox.setCurrentIndex(0)

    @state_node
    def showSelectedSpectrum(self):
        workspace =self.current_workspace
        index = workspace.selected_spectrum_index
        spectrum_info = next(iter(workspace.spectra_list.file_spectrum_info_list[index]))

