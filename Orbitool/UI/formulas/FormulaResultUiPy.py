from copy import deepcopy
from typing import List

from PyQt6 import QtCore, QtWidgets
from pyteomics.mass.mass import isotopologues

from Orbitool.models.formula import Formula
from Orbitool.models.spectrum import FittedPeak
from Orbitool.UI.component import Plot
from Orbitool.UI.manager import Manager, state_node
from Orbitool.UI.utils import get_tablewidget_selected_row
from Orbitool.utils import binary_search

from . import FormulaResultUi


class Window(QtWidgets.QMainWindow):
    acceptSignal = QtCore.pyqtSignal(list)

    def __init__(self, manager: Manager, input: str, mass: float, formulas: List[Formula], peak_index: int) -> None:
        super().__init__()
        self.manager = manager
        self.ui = FormulaResultUi.Ui_MainWindow()
        self.setupUi()

        self.ui.lineEdit.setText(input)
        self.mass = mass
        self.formulas = deepcopy(formulas)
        self.peak_index = peak_index

        self.showResult()

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)

        ui.resultTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        ui.isotopesTableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.plot = Plot(ui.widget)
        ui.calcPushButton.clicked.connect(self.calc)
        ui.resultTableWidget.itemDoubleClicked.connect(self.plot_row)
        ui.isotopesTableWidget.itemDoubleClicked.connect(self.edit_peak)
        ui.showAllToolButton.clicked.connect(self.showResult)
        ui.closeToolButton.clicked.connect(self.close)
        ui.acceptToolButton.clicked.connect(self.accept)
        ui.acceptEmptyToolButton.clicked.connect(self.acceptEmpty)

    @classmethod
    def fromInputStr(cls, manager: Manager, input: str):
        return Window(manager, *calc(manager, input))

    @classmethod
    def fromFittedPeak(cls, manager: Manager, peak_index: int):
        peaks = manager.workspace.info.peak_fit_tab.peaks
        peak = peaks[peak_index]
        return Window(manager, str(peak.peak_position), peak.peak_position, peak.formulas, peak_index)

    def find_peak_index(self, mass):
        return binary_search.indexNearest(self.peaks, mass, method=peak_position)

    @property
    def peaks(self):
        return self.manager.workspace.info.peak_fit_tab.peaks

    @state_node
    def calc(self):
        input = self.ui.lineEdit.text()
        _, mass, formulas, peak_index = calc(self.manager, input)
        self.mass = mass
        self.formulas = formulas
        self.peak_index = peak_index
        self.showResult()

    @state_node(mode='x')
    def showResult(self):
        mass = self.mass
        formulas = self.formulas

        table: QtWidgets.QTableWidget = self.ui.resultTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(formulas))

        def ppm(m):
            return (m / mass - 1) * 1e6

        for index, formula in enumerate(formulas):
            def setText(column, text):
                table.setItem(index, column, QtWidgets.QTableWidgetItem(text))
            setText(0, str(formula))
            setText(1, format(formula.mass(), '.6f'))
            setText(2, format(ppm(formula.mass()), '.2f'))
            setText(3, format(formula.dbe(), '.1f'))
        table.resizeColumnsToContents()

        ax = self.plot.ax
        ax.clear()

        if self.peak_index:
            peak = self.peaks[self.peak_index]
            intensity = peak.peak_intensity
            ax.plot(peak.mz, peak.intensity)
        else:
            intensity = 1

        for f in self.formulas:
            m = f.mass()
            ax.plot([m, m], [0, intensity])
            ax.annotate(str(f), [m, intensity])

        self.plot.canvas.draw()

    @state_node(withArgs=True)
    def plot_row(self, item: QtWidgets.QTableWidgetItem):
        row = item.row()
        formula = self.formulas[row].findOrigin()
        origin = formula.absoluteAbundance()
        isotopes = [(Formula(isotope), abundance) for isotope, abundance in isotopologues(formula=str(formula.toStr(
            True, False)), isotope_threshold=origin * 2e-3, overall_threshold=origin * 1e-3, report_abundance=True)]

        first = isotopes.pop(0)
        isotopes.sort(key=lambda i: i[0].mass())
        isotopes.insert(0, first)

        rtol = self.manager.workspace.info.formula_docker.calc_gen.rtol

        mass = formula.mass()
        if len(self.peaks) > 0:
            peak_index = self.find_peak_index(mass)
            peak = self.peaks[peak_index]
            plot_peak = abs(peak.peak_position / mass - 1) < rtol
        else:
            plot_peak = False

        if plot_peak:
            intensity = peak.peak_intensity / origin
        else:
            intensity = 1 / origin

        table = self.ui.isotopesTableWidget
        table.clearContents()
        table.setRowCount(0)
        table.setRowCount(len(isotopes))

        ax = self.plot.ax
        ax.clear()

        for row, (isotope, abundance) in enumerate(isotopes):  # include original formula
            isotope.charge = formula.charge
            mass = isotope.mass()

            if plot_peak:
                peak_index = self.find_peak_index(mass)
                iso_peak = self.peaks[peak_index]
                if abs(iso_peak.peak_position / mass - 1) < rtol:
                    plot_iso_peak = True
                    ax.plot(iso_peak.mz, iso_peak.intensity)
                    ax.annotate(format(iso_peak.peak_position, '4f'), [
                                iso_peak.peak_position, 0])
                else:
                    plot_iso_peak = False
            else:
                plot_iso_peak = False

            iso_int = intensity * abundance
            ax.plot([mass, mass], [0, iso_int])
            ax.annotate(str(isotope), [mass, iso_int])

            def setText(col, text):
                table.setItem(row, col, QtWidgets.QTableWidgetItem(text))
            setText(0, str(isotope))
            setText(1, format(isotope.mass(), '.4f'))
            setText(3, format(abundance / origin, '.4f'))

            if not plot_iso_peak:
                continue
            setText(2, format((iso_peak.peak_position / mass - 1) * 1e6, '.2f'))
            setText(4, format(iso_peak.peak_intensity, '.2e'))
            setText(5, format(iso_peak.peak_intensity /
                    peak.peak_intensity, '.4f'))

        self.plot.canvas.draw()

    @state_node(withArgs=True)
    def edit_peak(self, item: QtWidgets.QTableWidgetItem):
        table = self.ui.isotopesTableWidget
        row = item.row()
        formula = Formula(table.item(row, 0).text())
        it = table.item(row, 2)
        if it and it.text():
            index = self.find_peak_index(formula.mass())
            from Orbitool.UI import PeakFitFloatUiPy
            win = PeakFitFloatUiPy.Window.get_or_create(self.manager, index)
            win.set_formulas(index, [formula])
            win.raise_()
            win.show()
            win.raise_()

    @state_node
    def accept(self):
        if len(self.formulas) <= 1:
            self.acceptSignal.emit(self.formulas)
            self.close()
            return

        indexes = get_tablewidget_selected_row(self.ui.resultTableWidget)
        if len(indexes) == 0:
            ret = QtWidgets.QMessageBox.question(
                self, "accept multi formulas?",
                "or select one formula to accept",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No)
            if ret == QtWidgets.QMessageBox.StandardButton.No:
                return
            formulas = self.formulas
        else:
            formulas = [self.formulas[index] for index in indexes]
        self.acceptSignal.emit(formulas)
        self.close()

    @state_node
    def acceptEmpty(self):
        self.acceptSignal.emit([])
        self.close()


def peak_position(peaks: List[FittedPeak], index: int):
    return peaks[index].peak_position


def calc(manager: Manager, input: str):
    info = manager.workspace.info
    try:
        mass = float(input)
        formulas = info.formula_docker.calc_gen.generate().get(mass, info.formula_docker.charge)
    except ValueError:
        formula = Formula(input)
        formulas = [formula]
        mass = formula.mass()

    peaks = info.peak_fit_tab.peaks

    if len(peaks) > 0:
        index = binary_search.indexNearest(
            peaks, mass, method=peak_position)
        peak = peaks[index]
        peak_index = index if abs(mass) > 1e-6 and abs(
            peak.peak_position / mass - 1) < 3e-8 else None
    else:
        peak_index = None

    formulas.sort(key=lambda f: abs(f.mass() / mass - 1))

    return input, mass, formulas, peak_index
