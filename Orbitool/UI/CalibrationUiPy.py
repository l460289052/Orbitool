from typing import Union, Optional, Generator, Iterable, List, Tuple
import numpy as np
from . import CalibrationUi
from .manager import Manager, state_node, MultiProcess
from PyQt5 import QtWidgets, QtCore
from ..utils.formula import Formula
from ..structures.HDF5 import StructureConverter
from ..structures.file import SpectrumInfo
from ..structures.spectrum import Spectrum
from ..structures.workspace import WorkSpace
from ..structures.workspace.calibration import Ion
from .utils import get_tablewidget_selected_row
from ..functions import spectrum as spectrum_func


class ReadFromFile(MultiProcess):
    @staticmethod
    def func(data: Tuple[SpectrumInfo, Tuple[np.ndarray, np.ndarray, float]], **kwargs):
        info, (mz, intensity, time) = data
        mz, intensity = spectrum_func.removeZeroPositions(mz, intensity)
        spectrum = Spectrum(file_path=info.file_path, mz=mz, intensity=intensity,
                            start_time=info.start_time, end_time=info.end_time)
        return spectrum

    @ staticmethod
    def read(file, infos: List[SpectrumInfo], **kwargs) -> Generator:
        for info in infos:
            yield info, info.get_spectrum_from_info(with_minutes=True)

    @ staticmethod
    def write(file: WorkSpace, rets: Iterable[Spectrum], dest, **kwargs):
        tmp = file._obj.create_group("tmp")
        for index, spectrum in enumerate(rets):
            StructureConverter.write_to_h5(tmp, str(index), spectrum)

        if dest in file:
            del file[dest]
        file._obj.move(tmp.name, dest)

    @ staticmethod
    def exception(file, **kwargs):
        if "tmp" in file:
            del file["tmp"]


class Widget(QtWidgets.QWidget, CalibrationUi.Ui_Form):
    def __init__(self, manager: Manager) -> None:
        super().__init__()
        self.manager: Manager = manager
        self.setupUi(self)

        manager.inited.connect(self.init)

    def setupUi(self, Form):
        super().setupUi(Form)

        self.addIonToolButton.clicked.connect(self.addIon)
        self.delIonToolButton.clicked.connect(self.removeIon)
        self.calcInfoPushButton.clicked.connect(self.calcInfo)

    @ property
    def calibration(self):
        return self.manager.workspace.calibration_tab

    def init(self):
        ions = ['C5H6O9N-', 'C2HO4-', 'C3H4O7N-']
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

        rtol = self.rtolDoubleSpinBox.value() / 1e-6
        degree = self.degreeSpinBox.value()
        useNIons = self.nIonsSpinBox.value()

        dest = '/'.join([workspace.calibration_tab._obj.name, "raw_spectrums"])
        read_from_file = ReadFromFile(
            workspace, {"infos": workspace.spectra_list.info.file_spectrum_info_list, "dest": dest}, self.manager.pool)
        yield read_from_file

        length = len(workspace.calibration_tab._obj["raw_spectrums"])
