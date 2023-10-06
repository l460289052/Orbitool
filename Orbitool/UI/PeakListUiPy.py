from array import array
import contextlib
import csv
from typing import Dict, List, Optional, Tuple, Union, cast

from PyQt6 import QtCore, QtGui, QtWidgets

from Orbitool.models.formula import Formula
from Orbitool.models.spectrum import FittedPeak, PeakTags
from Orbitool.utils import binary_search

from .. import setting
from . import PeakListUi
from .manager import Manager, state_node
from .PeakFitFloatUiPy import Window as PeakFloatWin
from .utils import get_tablewidget_selected_row, savefile

colors = {
    PeakTags.Done: QtGui.QColor(0xD9FFC9),
    PeakTags.Noise: QtGui.QColor(0xC6C6C6),
    PeakTags.Fail: QtGui.QColor(0xFFBBB1)}


class Widget(QtWidgets.QWidget):

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        manager.init_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)

        manager.signals.peak_list_show.connect(self.showPeaks)
        manager.getters.peak_list_selected_true_index.connect(self.getSelected)

        self.ui = PeakListUi.Ui_Form()
        self.setupUi()

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)

        ui.doubleSpinBox.setKeyboardTracking(False)
        ui.doubleSpinBox.valueChanged.connect(self.goto_mass)
        ui.gotoToolButton.clicked.connect(self.goto_mass)
        ui.tableWidget.itemDoubleClicked.connect(self.openPeakFloatWin)
        ui.tableWidget.verticalScrollBar().valueChanged.connect(self.scrolled)

        self.manager.bind.peak_fit_left_index.connect(
            "peaklist", self.scroll_to_index)

        ui.exportSpectrumPushButton.clicked.connect(self.exportSpectrum)
        ui.exportPeaksPushButton.clicked.connect(self.exportPeaks)
        ui.exportIsotopePushButton.clicked.connect(self.exportIsotopes)

    def restore(self):
        self.info.ui_state.restore_state(self.ui)

    def updateState(self):
        self.info.ui_state.store_state(self.ui)

    @property
    def info(self):
        return self.manager.workspace.info.peak_fit_tab

    def showPeaks(self):
        table = self.ui.tableWidget
        peaks = self.info.peaks
        original_indexes = self.info.original_indexes
        raw_split_num = self.info.raw_split_num
        indexes = self.info.shown_indexes

        peaks = [peaks[index] for index in indexes]

        bar = table.verticalScrollBar()
        item = table.verticalHeaderItem(bar.value())
        if item:
            current_index = int(item.text())
        else:
            current_index = 0

        with self.no_send_slider():
            table.clearContents()
            table.setRowCount(0)
            table.setRowCount(len(peaks))
            table.setVerticalHeaderLabels(map(str, indexes))
            ind = binary_search.indexNearest(indexes, current_index)
            bar.setRange(0, len(indexes))
            bar.setSliderPosition(ind)

        for index, peak in enumerate(peaks):
            tag = peak.tags
            if tag:
                tag = PeakTags(tag[0])
            c = colors.get(tag, None)

            def setItem(column, msg):
                item = QtWidgets.QTableWidgetItem(str(msg))
                if c is not None:
                    item.setBackground(c)
                table.setItem(
                    index, column, item)

            setItem(0, format(peak.peak_position, '.5f'))
            setItem(1, ', '.join(str(f) for f in peak.formulas))
            setItem(2, format(peak.peak_intensity, '.3e'))
            setItem(3,
                    format((peak.peak_position / peak.formulas[0].mass() - 1) * 1e6, '.5f') if len(peak.formulas) == 1 else "")
            setItem(4, format(peak.area, '.3e'))
            setItem(5, ','.join(tag.name for tag in map(PeakTags, peak.tags)))

            setItem(6, raw_split_num[original_indexes[indexes[index]]])

    @contextlib.contextmanager
    def no_send_slider(self):
        bar = self.ui.tableWidget.verticalScrollBar()
        box = self.ui.bindPlotCheckBox
        value = box.isChecked()
        box.setChecked(False)
        yield
        box.setChecked(value)

    def filterSelected(self, select: bool):
        """
            filter selected or filter unselected
        """
        selectedindex = get_tablewidget_selected_row(self.ui.tableWidget)
        info = self.info
        indexes = info.shown_indexes
        if select:
            info.shown_indexes = [indexes[index] for index in selectedindex]
        else:
            for index in reversed(selectedindex):
                indexes.pop(index)

    def getSelected(self):
        selectedindex = get_tablewidget_selected_row(self.ui.tableWidget)
        info = self.info
        indexes = info.shown_indexes
        return [indexes[index] for index in selectedindex]

    @state_node
    def goto_mass(self):
        mass = self.ui.doubleSpinBox.value()
        peaks = self.info.peaks
        indexes = self.info.shown_indexes
        index = binary_search.indexNearest(
            indexes, mass, method=lambda indexes, ind: peaks[indexes[ind]].peak_position)
        self.scroll_to_index(index)
        self.manager.bind.peak_fit_left_index.emit_except("peaklist", index)

    @state_node(mode='n', withArgs=True)
    def scrolled(self, index):
        if self.ui.bindPlotCheckBox.isChecked():
            self.manager.bind.peak_fit_left_index.emit_except(
                "peaklist", index)

    def scroll_to_index(self, index):
        if self.ui.bindPlotCheckBox.isChecked():
            with self.no_send_slider():
                self.ui.tableWidget.verticalScrollBar().setSliderPosition(index)

    @state_node(withArgs=True)
    def openPeakFloatWin(self, item: QtWidgets.QTableWidgetItem):
        row = item.row()
        win = PeakFloatWin.get_or_create(
            self.manager, self.info.shown_indexes[row])
        win.show()
        win.raise_()

    @state_node
    def exportSpectrum(self):
        spectrum = self.info.spectrum
        ret, f = savefile(
            "Save Spectrum", "CSV file(*.csv)",
            f"fitted_spectrum {spectrum.start_time.strftime(setting.general.export_time_format)}-"
            f"{spectrum.end_time.strftime(setting.general.export_time_format)}")

        if not ret:
            return

        with open(f, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['mz', 'intensity'])
            writer.writerows(zip(spectrum.mz, spectrum.intensity))

    @state_node
    def exportPeaks(self):
        info = self.info
        spectrum = info.spectrum

        ret, f = savefile(
            "Save Peak List", "CSV file(*.csv)",
            f"peak_list {spectrum.start_time.strftime(setting.general.export_time_format)}"
            f"-{spectrum.end_time.strftime(setting.general.export_time_format)}")
        if not ret:
            return

        peaks = info.peaks
        indexes = info.shown_indexes
        peaks: List[FittedPeak] = [peaks[index] for index in indexes]
        raw_split_num = info.raw_split_num
        orginal_indexes = info.original_indexes

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
                    '/'.join([str(formula.dbe())
                              for formula in peak.formulas]),
                    (peak.peak_position /
                     peak.formulas[0].mass() - 1) if len(peak.formulas) == 1 else '',
                    raw_split_num[orginal_indexes[indexes[index]]]])

    @state_node
    def exportIsotopes(self):
        info = self.info
        spectrum = info.spectrum

        ret, f = savefile(
            "Save Isotopes", "CSV file(*.csv)",
            f"isotope {spectrum.start_time.strftime(setting.general.export_time_format)}"
            f"-{spectrum.end_time.strftime(setting.general.export_time_format)}")
        if not ret:
            return

        peaks = info.peaks
        shown_indexes = cast(array[int], info.shown_indexes)

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
