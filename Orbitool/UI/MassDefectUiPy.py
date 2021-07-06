from typing import Optional, Union
import math

import numpy as np
from PyQt5 import QtCore, QtWidgets
from matplotlib.cm import rainbow as rainbow_color_map
from matplotlib.figure import Figure

from ..structures.spectrum import FittedPeak
from . import MassDefectUi
from .component import Plot
from .manager import Manager, state_node


class Widget(QtWidgets.QWidget, MassDefectUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager
        self.setupUi(self)
        self.plot = Plot(self.widget)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.plotPushButton.clicked.connect(self.plotMassDefect)

    def calculateMassDefect(self):
        is_dbe = self.dbeRadioButton.isChecked()
        gry = self.showGreyCheckBox.isChecked()

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

        if gry:
            gry_peaks = [peak for peak in peaks if len(peak.formulas) == 0]
            gry_x = np.array([peak.peak_position for peak in peaks])
            gry_y = gry_x - np.round(gry_x)
            gry_size = np.array([peak.peak_intensity for peak in peaks])
        else:
            gry_size = gry_y = gry_x = np.zeros(0, dtype=float)

        return (clr_x, clr_y, clr_size, clr_color), (gry_x, gry_y, gry_size)

    @state_node
    def plotMassDefect(self):
        plot = self.plot
        plot.clear()

        min_factor = math.exp(
            self.minSizeHorizontalSlider.value() / 20.)
        max_factor = math.exp(
            self.maxSizeHorizontalSlider.value() / 20.)

        is_dbe = self.dbeRadioButton.isChecked()
        is_log = self.logCheckBox.isChecked()
        (clr_x, clr_y, clr_size, clr_color), (gry_x,
                                              gry_y, gry_size) = self.calculateMassDefect()

        if is_log:
            clr_size = np.log(clr_size + 1) - 1
            gry_size = np.log(gry_size + 1) - 1

        if len(gry_x) > 0:
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
        ax.clear()
        gry_size /= maximum
        gry_size[gry_size < minimum] = minimum
        ax.scatter(gry_x, gry_y, s=gry_size, c='grey',
                   linewidths=0.5, edgecolors='k')

        clr_size /= maximum
        clr_size[clr_size < minimum] = minimum
        sc = ax.scatter(clr_x, clr_y, s=clr_size, c=clr_color,
                        cmap=rainbow_color_map, linewidths=0.5, edgecolors='k')
        clrb = plot.fig.colorbar(sc)
        element = self.elementLineEdit.text()
        clrb.ax.set_title('DBE' if is_dbe else f'Element {element}')

        ax.autoscale(True)
        plot.fig.tight_layout()

        plot.canvas.draw()


def find_formula(peak: FittedPeak):
    tols: np.ndarray = abs(
        np.array([peak.peak_position / f.mass() - 1 for f in peak.formulas]))
    argmin = tols.argmin()
    return peak.formulas[argmin]
