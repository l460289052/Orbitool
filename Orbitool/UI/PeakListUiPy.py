import csv
from typing import Dict, List, Optional, Tuple, Union

from PyQt5 import QtCore, QtWidgets

from ..config import exportTimeFormat
from ..functions import binary_search
from ..structures.spectrum import FittedPeak
from ..utils.formula import Formula
from . import PeakListUi
from .manager import Manager, state_node
from .PeakFitFloatUiPy import Window as PeakFloatWin
from .utils import get_tablewidget_selected_row, savefile


class Widget(QtWidgets.QWidget, PeakListUi.Ui_Form):
    peak_refit_finish = QtCore.pyqtSignal()

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.doubleSpinBox.setKeyboardTracking(False)
        self.doubleSpinBox.valueChanged.connect(self.goto_mass)
        self.gotoToolButton.clicked.connect(self.goto_mass)
        self.tableWidget.itemDoubleClicked.connect(self.openPeakFloatWin)
        self.tableWidget.verticalScrollBar().valueChanged.connect(self.scrolled)

        self.manager.bind.peak_fit_left_index.connect(
            "peaklist", self.scroll_to_index)

        self.peak_float: PeakFloatWin = None

        self.exportSpectrumPushButton.clicked.connect(self.exportSpectrum)
        self.exportPeaksPushButton.clicked.connect(self.exportPeaks)
        self.exportIsotopePushButton.clicked.connect(self.exportIsotopes)

    @property
    def peaks_info(self):
        return self.manager.workspace.peakfit_tab.info

    def showPeaks(self):
        table = self.tableWidget
        peaks = self.peaks_info.peaks
        original_indexes = self.peaks_info.original_indexes
        raw_split_num = self.peaks_info.raw_split_num
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
            setItem(2, format(peak.peak_intensity, '.3e'))
            if len(peak.formulas) == 1:
                setItem(3,
                        format((peak.peak_position / peak.formulas[0].mass() - 1) * 1e6, '.5f'))
            setItem(4, format(peak.area, '.3e'))

            setItem(5, raw_split_num[original_indexes[indexes[index]]])

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

    @state_node
    def goto_mass(self):
        mass = self.doubleSpinBox.value()
        peaks = self.peaks_info.peaks
        indexes = self.peaks_info.shown_indexes
        index = binary_search.indexNearest(
            indexes, mass, method=lambda indexes, ind: peaks[indexes[ind]].peak_position)
        self.scroll_to_index(index)
        self.manager.bind.peak_fit_left_index.emit_except("peaklist", index)

    def scrolled(self, index):
        if self.bindPlotCheckBox.isChecked():
            self.manager.bind.peak_fit_left_index.emit_except(
                "peaklist", index)

    def scroll_to_index(self, index):
        if self.bindPlotCheckBox.isChecked():
            self.tableWidget.verticalScrollBar().setSliderPosition(index)

    @state_node(withArgs=True)
    def openPeakFloatWin(self, item: QtWidgets.QTableWidgetItem):
        row = item.row()
        if self.peak_float is not None and not self.peak_float.isHidden():
            self.peak_float.close()
        widget = PeakFloatWin(
            self.manager, self.peaks_info.shown_indexes[row])
        widget.callback.connect(self.peak_refit_finish.emit)
        self.peak_float = widget
        widget.show()

    @state_node
    def exportSpectrum(self):
        spectrum = self.peaks_info.spectrum
        ret, f = savefile("Save Spectrum", "CSV file(*.csv)",
                          f"fitted_spectrum {spectrum.start_time.strftime(exportTimeFormat)}-"
                          f"{spectrum.end_time.strftime(exportTimeFormat)}")

        if not ret:
            return

        with open(f, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['mz', 'intensity'])
            writer.writerows(zip(spectrum.mz, spectrum.intensity))

    @state_node
    def exportPeaks(self):
        spectrum = self.peaks_info.spectrum

        ret, f = savefile("Save Peak List", "CSV file(*.csv)",
                          f"peak_list {spectrum.start_time.strftime(exportTimeFormat)}"
                          f"-{spectrum.end_time.strftime(exportTimeFormat)}")
        if not ret:
            return

        peaks = self.peaks_info.peaks
        indexes = self.peaks_info.shown_indexes
        peaks = [peaks[index] for index in indexes]
        raw_split_num = self.peaks_info.raw_split_num
        orginal_indexes = self.peaks_info.original_indexes
        calc = self.manager.workspace.formula_docker.info.restricted_calc

        with open(f, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['mz', 'intensity', 'area',
                             'formula', 'DBE', 'rtol', 'peaks num'])
            for index, peak in enumerate(peaks):
                writer.writerow([
                    peak.peak_position,
                    peak.peak_intensity,
                    peak.area,
                    '/'.join([str(formula) for formula in peak.formulas]),
                    '/'.join([str(calc.getFormulaDBE(formula))
                              for formula in peak.formulas]),
                    (peak.peak_position /
                     peak.formulas[0].mass() - 1) if len(peak.formulas) == 1 else '',
                    raw_split_num[orginal_indexes[indexes[index]]]])

    @state_node
    def exportIsotopes(self):
        spectrum = self.peaks_info.spectrum

        ret, f = savefile("Save Isotopes", "CSV file(*.csv)",
                          f"isotope {spectrum.start_time.strftime(exportTimeFormat)}"
                          f"-{spectrum.end_time.strftime(exportTimeFormat)}")
        if not ret:
            return

        peaks = self.peaks_info.peaks
        shown_indexes = self.peaks_info.shown_indexes

        formula_map: Dict[Formula, List[Tuple[int, Formula]]] = {}
        for index, peak in enumerate(peaks):
            for formula in peak.formulas:
                if formula.isIsotope:
                    formula_map.setdefault(
                        formula.findOrigin(), []).append((index, formula))

        with open(f, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['formula', 'measured mz', 'intensity',
                             'intensity ratio', 'theoretic ratio'])

            for index in shown_indexes:
                peak = peaks[index]

                formulas = [f for f in peak.formulas if not f.isIsotope]
                if not formulas:
                    continue

                isotopes = [formula_map.get(formula, [])
                            for formula in formulas]
                isotopes = sum(isotopes, [])
                writer.writerow(['/'.join(str(f) for f in formulas),
                                 peak.peak_position, peak.peak_intensity, 1, 1])

                for i, isotope in isotopes:
                    i_peak = peaks[i]
                    writer.writerow([str(isotope), i_peak.peak_position, i_peak.peak_intensity,
                                     i_peak.peak_intensity / peak.peak_intensity, isotope.relativeAbundance()])

                writer.writerow([''])
