import csv
import math
from typing import Optional, Union

import numpy as np
from matplotlib.cm import rainbow as rainbow_color_map
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtWidgets

from ..structures.spectrum import FittedPeak
from . import MassDefectUi
from .component import Plot
from .manager import Manager, state_node
from .utils import savefile


class Widget(QtWidgets.QWidget, MassDefectUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        self.plot = Plot(self.widget)

        manager.inited_or_restored.connect(self.plotMassDefect)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.calcPushButton.clicked.connect(self.calc)
        self.exportPushButton.clicked.connect(self.export)

        self.logCheckBox.toggled.connect(self.replot)
        self.showGreyCheckBox.toggled.connect(self.replot)
        self.minSizeHorizontalSlider.valueChanged.connect(self.replot)
        self.maxSizeHorizontalSlider.valueChanged.connect(self.replot)

    @property
    def massdefect(self):
        return self.manager.workspace.massdefect_tab.info

    @state_node
    def calc(self):
        self.calculateMassDefect()
        self.plotMassDefect()

    def calculateMassDefect(self):
        is_dbe = self.dbeRadioButton.isChecked()

        calc = self.manager.workspace.formula_docker.info.restricted_calc
        peaks = self.manager.workspace.peakfit_tab.info.peaks

        clr_peaks = [peak for peak in peaks if len(peak.formulas) > 0]
        clr_formula = list(map(find_formula, clr_peaks))

        if is_dbe:
            clr_color = [calc.getFormulaDBE(f) for f in clr_formula]
            clr_color = np.array(clr_color, dtype=float)
        else:
            element = self.elementLineEdit.text()
            clr_color = [f[element] for f in clr_formula]
            clr_color = np.array(clr_color, dtype=int)

        clr_x = [peak.peak_position for peak in clr_peaks]
        clr_x = np.array(clr_x, dtype=float)
        clr_y = clr_x - np.round(clr_x)
        clr_size = np.array(
            [peak.peak_intensity for peak in clr_peaks], dtype=float)

        gry_peaks = [peak for peak in peaks if len(peak.formulas) == 0]
        gry_x = np.array([peak.peak_position for peak in gry_peaks])
        gry_y = gry_x - np.round(gry_x)
        gry_size = np.array([peak.peak_intensity for peak in gry_peaks])

        info = self.massdefect
        info.is_dbe = is_dbe
        if is_dbe:
            info.element = ""
        else:
            info.element = element
        info.clr_x, info.clr_y, info.clr_size, info.clr_color = clr_x, clr_y, clr_size, clr_color
        info.gry_x, info.gry_y, info.gry_size = gry_x, gry_y, gry_size

    def plotMassDefect(self):
        plot = self.plot
        plot.clear()

        info = self.massdefect
        if len(info.clr_x) == 0 and len(info.gry_x) == 0:
            return

        min_factor = math.exp(
            self.minSizeHorizontalSlider.value() / 20.)
        max_factor = math.exp(
            self.maxSizeHorizontalSlider.value() / 20.)

        is_dbe = info.is_dbe
        gry = self.showGreyCheckBox.isChecked()
        is_log = self.logCheckBox.isChecked()

        clr_x, clr_y, clr_size, clr_color = info.clr_x, info.clr_y, info.clr_size, info.clr_color
        gry_x, gry_y, gry_size = info.gry_x, info.gry_y, info.gry_size

        if is_log:
            clr_size = np.log(clr_size + 1) - 1
            gry_size = np.log(gry_size + 1) - 1

        if gry and len(gry_x) > 0:
            maximum = np.max((clr_size.max(), gry_size.max()))
        else:
            maximum = clr_size.max()

        if is_log:
            maximum /= 70
        else:
            maximum /= 200
        maximum /= max_factor
        minimum = 5 * min_factor

        ax = plot.ax
        if gry:
            gry_size /= maximum
            gry_size[gry_size < minimum] = minimum
            ax.scatter(gry_x, gry_y, s=gry_size, c='grey',
                       linewidths=0.5, edgecolors='k')

        clr_size /= maximum
        clr_size[clr_size < minimum] = minimum
        sc = ax.scatter(clr_x, clr_y, s=clr_size, c=clr_color,
                        cmap=rainbow_color_map, linewidths=0.5, edgecolors='k')
        clrb = plot.fig.colorbar(sc)
        element = info.element
        clrb.ax.set_title('DBE' if is_dbe else f'Element {element}')

        ax.autoscale(True)
        plot.fig.tight_layout()

        plot.canvas.draw()

    @state_node
    def replot(self):
        self.plotMassDefect()

    @state_node
    def export(self):
        info = self.massdefect
        prefer = "dbe" if info.is_dbe else f"element {info.element}"
        ret, f = savefile("Mass Defect", "CSV file(*.csv)", prefer)

        if not ret:
            return

        with open(f, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['x', 'mass defect', 'intensity', 'color'])

            writer.writerows(zip(info.clr_x, info.clr_y,
                                 info.clr_size, info.clr_color))
            writer.writerows(zip(info.gry_x, info.gry_y, info.gry_size))


def find_formula(peak: FittedPeak):
    tols: np.ndarray = abs(
        np.array([peak.peak_position / f.mass() - 1 for f in peak.formulas]))
    argmin = tols.argmin()
    return peak.formulas[argmin]
