from typing import Optional

from PyQt5 import QtCore, QtWidgets

from ..functions import spectrum as spectrum_func
from . import PeakFitUi
from .manager import Manager


class Widget(QtWidgets.QWidget, PeakFitUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.showSelectedPushButton.clicked.connect(self.showSelect)

    def showSelect(self):
        workspace = self.manager.workspace

        def read_split_fit_calc(self):
            spectrum = workspace.calibration_tab.calibrated_spectra[
                workspace.spectra_list.info.selected_index]
            raw_peaks = spectrum_func.splitPeaks(
                spectrum.mz, spectrum.intensity)
            peaks = list(
                map(workspace.peak_shape_tab.info.func.splitPeak, raw_peaks))

        # spectrum
        # peak list
        # plot
        pass
