from Orbitool.utils.readers import ThermoFile
from PyQt5 import QtWidgets

class TestThermo:
    def setup_class(self):
        f, _ = QtWidgets.QFileDialog.getOpenFileName(directory="./..")
        self.f = ThermoFile(f)

    def test_average(self):
        self.f.getAveragedSpectrum(1e-6,None,(1,10))