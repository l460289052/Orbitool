from typing import Optional, Union

from PyQt5 import QtCore, QtWidgets

from . import PeakListUi
from .manager import Manager
from ..structures.spectrum import FittedPeak
from .utils import get_tablewidget_selected_row


class Widget(QtWidgets.QWidget, PeakListUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)

    @property
    def peaks_info(self):
        return self.manager.workspace.peakfit_tab.info

    def showPeaks(self):
        table = self.tableWidget
        peaks = self.peaks_info.peaks
        indexes = self.peaks_info.shown_indexes
        peaks = [peaks[index] for index in indexes]
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(peaks))
        table.setVerticalHeaderLabels(map(str, indexes))

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

    def filterSelected(self, select: bool):
        """
            filter selected or filter unselected
        """
        selectedindex = get_tablewidget_selected_row(self.tableWidget)
        info = self.peaks_info
        indexes = info.shown_indexes
        if select:
            info.shown_indexes = [indexes[index] for index in selectedindex]
        else:
            for index in reversed(selectedindex):
                indexes.pop(index)
