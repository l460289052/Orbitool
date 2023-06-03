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


class Widget(QtWidgets.QWidget):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager = manager

        self.ui = MassDefectUi.Ui_Form()
        self.setupUi()
        self.plot = Plot(self.ui.widget)

        manager.init_or_restored.connect(self.restore)
        manager.save.connect(self.updateState)

    def setupUi(self):
        ui = self.ui
        ui.setupUi(self)

        ui.calcPushButton.clicked.connect(self.calc)
        ui.exportPushButton.clicked.connect(self.export)

        ui.transparencyDoubleSpinBox.valueChanged.connect(self.replot)
        ui.logCheckBox.toggled.connect(self.replot)
        ui.showGreyCheckBox.toggled.connect(self.replot)
        ui.minSizeHorizontalSlider.valueChanged.connect(self.replot)
        ui.maxSizeHorizontalSlider.valueChanged.connect(self.replot)

    def restore(self):
        self.info.ui_state.restore_state(self.ui)
        self.plotMassDefect()

    def updateState(self):
        self.info.ui_state.store_state(self.ui)

    @property
    def info(self):
        return self.manager.workspace.info.mass_defect_tab

    @state_node
    def calc(self):
        self.calculateMassDefect()
        self.plotMassDefect()

    def calculateMassDefect(self):
        ui = self.ui
        is_dbe = ui.dbeRadioButton.isChecked()
        is_ele = ui.elementRadioButton.isChecked()
        is_atom = ui.atomsRadioButton.isChecked()

        peaks = self.manager.workspace.info.peak_fit_tab.peaks

        clr_peaks = [peak for peak in peaks if len(peak.formulas) > 0]
        clr_formula = list(map(find_formula, clr_peaks))

        if is_dbe:
            clr_color = [f.dbe() for f in clr_formula]
            clr_color = np.array(clr_color, dtype=float)
            clr_labels = None
        elif is_ele:
            element = ui.elementLineEdit.text()
            clr_color = [f[element] for f in clr_formula]
            clr_color = np.array(clr_color, dtype=int)
            clr_labels = None
        elif is_atom:
            atoms = {f.atoms() for f in clr_formula}
            atoms = list(atoms)
            atoms.sort(key=lambda f: (len(f), f.mass()))
            atoms_index = {atom: ind for ind, atom in enumerate(atoms)}
            clr_color = [atoms_index[f.atoms()] for f in clr_formula]
            clr_color = np.array(clr_color, dtype=int)
            clr_labels = list(map(str, atoms))

        clr_x = [peak.peak_position for peak in clr_peaks]
        clr_x = np.array(clr_x, dtype=float)
        clr_y = clr_x - np.round(clr_x)
        clr_size = np.array(
            [peak.peak_intensity for peak in clr_peaks], dtype=float)

        gry_peaks = [peak for peak in peaks if len(peak.formulas) == 0]
        gry_x = np.array([peak.peak_position for peak in gry_peaks])
        gry_y = gry_x - np.round(gry_x)
        gry_size = np.array([peak.peak_intensity for peak in gry_peaks])

        info = self.info
        info.is_dbe = is_dbe
        if is_dbe:
            info.clr_title = "DBE"
        elif is_ele:
            info.clr_title = element
        elif is_atom:
            info.clr_title = "atoms"

        info.clr_x, info.clr_y, info.clr_size, info.clr_color, info.clr_labels = clr_x, clr_y, clr_size, clr_color, clr_labels
        info.gry_x, info.gry_y, info.gry_size = gry_x, gry_y, gry_size

    def plotMassDefect(self):
        plot = self.plot
        plot.clear()

        info = self.info
        if len(info.clr_x) == 0 and len(info.gry_x) == 0:
            return

        ui = self.ui

        if ui.minSizeHorizontalSlider.value() > ui.maxSizeHorizontalSlider.value():
            ui.minSizeHorizontalSlider.setValue(
                ui.maxSizeHorizontalSlider.value())  # will call replot
            return

        min_factor = math.exp(
            ui.minSizeHorizontalSlider.value() / 10) * 10
        max_factor = math.exp(
            ui.maxSizeHorizontalSlider.value() / 10) * 10

        is_dbe = info.is_dbe
        gry = ui.showGreyCheckBox.isChecked()
        is_log = ui.logCheckBox.isChecked()
        alpha = 1 - ui.transparencyDoubleSpinBox.value()

        clr_x, clr_y, clr_size, clr_color, clr_labels = info.clr_x, info.clr_y, info.clr_size, info.clr_color, info.clr_labels
        gry_x, gry_y, gry_size = info.gry_x, info.gry_y, info.gry_size

        if is_log:
            clr_size = np.log(clr_size + 1) - 1
            gry_size = np.log(gry_size + 1) - 1

        if gry and len(gry_x) > 0:
            maximum = np.max((clr_size.max(), gry_size.max()))
            minimum = np.min((clr_size.min(), gry_size.min()))
        else:
            maximum = clr_size.max()
            minimum = clr_size.min()

        # if is_log:
        #     maximum /= 70
        # else:
        #     maximum /= 200
        # maximum /= max_factor
        # minimum = 5 * min_factor

        ax = plot.ax
        if gry:
            gry_size = (gry_size - minimum) / (maximum - minimum) * \
                (max_factor - min_factor) + min_factor
            ax.scatter(gry_x, gry_y, s=gry_size, c='grey',
                       linewidths=0.5, edgecolors='k', alpha=alpha)

        clr_size = (clr_size - minimum) / (maximum - minimum) * \
            (max_factor - min_factor) + min_factor
        sc = ax.scatter(clr_x, clr_y, s=clr_size, c=clr_color,
                        cmap=rainbow_color_map, linewidths=0.5, edgecolors='k', alpha=alpha)
        clrb = plot.fig.colorbar(sc)
        clrb.ax.set_title(info.clr_title)
        if clr_labels is not None:
            clrb.ax.set_yticklabels(clr_labels)

        ax.autoscale(True)
        plot.fig.tight_layout()

        plot.canvas.draw()

    @state_node(mode='n')
    def replot(self):
        ax = self.plot.ax
        x = ax.get_xlim()
        y = ax.get_ylim()
        self.plotMassDefect()
        ax = self.plot.ax
        ax.set_xlim(*x)
        ax.set_ylim(*y)
        self.plot.canvas.draw()

    @state_node
    def export(self):
        info = self.info
        ret, f = savefile("Mass Defect", "CSV file(*.csv)", info.clr_title)

        if not ret:
            return

        if info.clr_title == "atoms":
            atoms = info.clr_labels

            def conv(value):
                return atoms[value]
        else:
            def conv(value):
                return value

        with open(f, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['x', 'mass defect', 'intensity', 'color'])

            writer.writerows(zip(info.clr_x, info.clr_y,
                                 info.clr_size, map(conv, info.clr_color)))
            writer.writerows(zip(info.gry_x, info.gry_y, info.gry_size))


def find_formula(peak: FittedPeak):
    tols: np.ndarray = abs(
        np.array([peak.peak_position / f.mass() - 1 for f in peak.formulas]))
    argmin = tols.argmin()
    return peak.formulas[argmin]
