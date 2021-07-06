from typing import Optional, Union

from PyQt5 import QtCore, QtWidgets

from . import PeakListUi
from .manager import Manager
from ..structures.spectrum import FittedPeak


class Widget(QtWidgets.QWidget, PeakListUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)

    @property
    def peaks(self):
        return self.manager.workspace.peakfit_tab.info.peaks

    def showPeaks(self):
        table = self.tableWidget
        peaks = self.peaks
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(peaks))
        for index, peak in enumerate(peaks):
            def setItem(column, msg):
                table.setItem(
                    index, column, QtWidgets.QTableWidgetItem(str(msg)))
            setItem(0, format(peak.peak_position, '.5f'))
            setItem(1, ', '.join(str(f) for f in peak.formulas))
            setItem(2, format(peak.peak_intensity, '.5e'))
            if len(peak.formulas) == 1:
                setItem(3,
                        format((peak.peak_position / peak.formulas[0].mass() - 1) * 1e6, '.3f'))
            setItem(4, format(peak.area, '.5e'))
            setItem(5, peak.split_num)
