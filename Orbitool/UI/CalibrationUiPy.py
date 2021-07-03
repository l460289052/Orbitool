from typing import Generator, Iterable, List, Optional, Tuple, Union, Dict
from datetime import datetime
import numpy as np
from PyQt5 import QtCore, QtWidgets
import h5py

from ..functions import spectrum as spectrum_func
from ..functions.peakfit.normal_distribution import NormalDistributionFunc
from ..functions.calibration import Calibrator, PolynomialRegressionFunc
from ..structures.file import SpectrumInfo
from ..structures.HDF5 import StructureConverter, StructureListView
from ..structures.spectrum import Spectrum
from ..workspace import WorkSpace
from ..workspace.calibration import Widget as CalibrationWidget
from ..utils.formula import Formula
from . import CalibrationUi
from .manager import Manager, MultiProcess, state_node
from .utils import get_tablewidget_selected_row
from .component import Plot


class ReadFromFile(MultiProcess):
    @staticmethod
    def func(data: Tuple[SpectrumInfo, Tuple[np.ndarray, np.ndarray, float]], **kwargs):
        info, (mz, intensity, time) = data
        mz, intensity = spectrum_func.removeZeroPositions(mz, intensity)
        spectrum = Spectrum(path=info.path, mz=mz, intensity=intensity,
                            start_time=info.start_time, end_time=info.end_time)
        return spectrum

    @ staticmethod
    def read(file, infos: List[SpectrumInfo], **kwargs) -> Generator:
        for info in infos:
            yield info, info.get_spectrum_from_info(with_minutes=True)

    @ staticmethod
    def write(file: WorkSpace, rets: Iterable[Spectrum], dest, **kwargs):
        tmp = StructureListView[Spectrum](file._obj, "tmp", True)
        tmp.h5_extend(rets)

        if dest in file:
            del file._obj[dest]
        return file._obj.move(tmp.h5_path, dest)

    @ staticmethod
    def exception(file, **kwargs):
        if "tmp" in file:
            del file["tmp"]


class SplitAndFitPeak(MultiProcess):
    @staticmethod
    def read(h5_spectra: StructureListView[Spectrum], **kwargs) -> Generator:
        return h5_spectra

    @staticmethod
    def func(data: Spectrum, fit_func: NormalDistributionFunc, ions: List[float], intensity_filter: float, **kwargs):
        ions_peak: List[Tuple[float, float]] = []
        for ion in ions:
            peak = fit_func.fetchNearestPeak(
                data, ion, intensity_filter)
            ions_peak.append(
                (peak.peak_position, peak.peak_intensity))

        return data.path, ions_peak

    @staticmethod
    def write(file, rets, **kwargs):
        path_ions_peak: Dict[str, List[List[Tuple[float, float]]]] = {}
        for path, ions_peak in rets:
            path_ions_peak.setdefault(path, []).append(ions_peak)
        return path_ions_peak


class Widget(QtWidgets.QWidget, CalibrationUi.Ui_Form):
    calcInfoFinished = QtCore.pyqtSignal()

    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager: Manager = manager
        self.setupUi(self)
        self.manager.calibrationPlot = self.plot
        manager.inited.connect(self.init)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.plot = Plot(self.widget)

        self.addIonToolButton.clicked.connect(self.addIon)
        self.delIonToolButton.clicked.connect(self.removeIon)
        self.calcInfoPushButton.clicked.connect(self.calcInfo)

    @ property
    def calibration(self):
        return self.manager.workspace.calibration_tab

    def init(self):
        ions = ["HNO3NO3-", "C6H3O2NNO3-", "C6H5O3NNO3-",
                "C6H4O5N2NO3-", "C8H12O10N2NO3-", "C10H17O10N3NO3-"]
        self.calibration.info.add_ions(ions)
        self.showIons()

    def showIons(self):
        info = self.calibration.info
        table = self.tableWidget
        table.clearContents()
        table.setRowCount(len(info.ions))
        for index, ion in enumerate(info.ions):
            table.setItem(index, 0, QtWidgets.QTableWidgetItem(ion.shown_text))
            table.setItem(
                index, 1, QtWidgets.QTableWidgetItem(format(ion.formula.mass(), ".4f")))

        table.show()

    @ state_node
    def addIon(self):
        self.calibration.info.add_ions(self.ionLineEdit.text().split(','))
        self.showIons()

    @ state_node
    def removeIon(self):
        indexes = get_tablewidget_selected_row(self.tableWidget)
        ions = self.calibration.info.ions
        for index in reversed(indexes):
            ions.pop(index)
        self.showIons()

    @ state_node
    def calcInfo(self):
        workspace = self.manager.workspace
        calibration_tab = self.calibration
        info = calibration_tab.info

        intensity_filter = 100
        rtol = self.rtolDoubleSpinBox.value() / 1e-6
        degree = self.degreeSpinBox.value()
        use_N_ions = self.nIonsSpinBox.value()

        # read file
        if not workspace.info.hasRead:
            read_from_file = ReadFromFile(
                workspace, {
                    "infos": workspace.spectra_list.info.file_spectrum_info_list,
                    "dest": calibration_tab.raw_spectra.h5_path})

            yield read_from_file
            workspace.info.hasRead = True

        h5_spectra = calibration_tab.raw_spectra
        fit_func = workspace.peak_shape_tab.info.func

        # use ions to decide whether to split
        need_to_split = True
        if len(info.calibrators) > 0:
            calculator = next(iter(info.calibrators.values()))
            calculated_ions = {ion.formula for ion in calculator.ions}
            now_ions = {ion.formula for ion in info.ions}
            if now_ions == calculated_ions:
                need_to_split = False

        if need_to_split:  # read ions from spectrum
            path_time = {
                path.path: path.createDatetime for path in workspace.info.pathlist}
            ions = [ion.formula.mass() for ion in info.ions]
            split_and_fit = SplitAndFitPeak(h5_spectra, dict(
                fit_func=fit_func, ions=ions, intensity_filter=intensity_filter))

            path_ions_peak: Dict[str, List[List[Tuple[float, float]]]] = yield split_and_fit

            def get_calibrator():
                path_calibrators: Dict[str, Calibrator] = {}

                for path, ions_peak in path_ions_peak.items():
                    ions_peak = np.array(ions_peak, dtype=float)
                    ions_position = ions_peak[:, :, 0]
                    ions_intensity = ions_peak[:, :, 1]
                    path_calibrators[path] = Calibrator.FactoryFromMzInt(
                        path_time[path], info.ions, ions_position, ions_intensity, rtol, use_N_ions)

                return path_calibrators

            info.calibrators = yield get_calibrator
        else:  # get info directly
            def get_calibrator_from_calibrator():
                return {path: calibrator.regeneratCalibrator(rtol=rtol, use_N_ions=use_N_ions) for path, calibrator in info.calibrators.items()}

            info.calibrators = yield get_calibrator_from_calibrator

        def generate_func_from_calibrator():
            ret = {}
            for path, calibrator in info.calibrators.items():
                min_index = calibrator.min_indexes
                func = PolynomialRegressionFunc.FactoryFit(
                    calibrator.ions_position[min_index], calibrator.ions_rtol[min_index], degree)
                ret[path] = func
            return ret
        info.poly_funcs = yield generate_func_from_calibrator

        self.calcInfoFinished.emit()
