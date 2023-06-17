from pathlib import Path
from .. import ThermoFile
from PyQt6 import QtWidgets

# class TestThermo:
#     def setup_class(self):
#         f, _ = QtWidgets.QFileDialog.getOpenFileName(directory="./..")
#         self.f = ThermoFile(f)

#     def test_average(self):
#         self.f.getAveragedSpectrum(1e-6,None,(1,10))

DATA_PATH = Path("C:/Users/liyih/OneDrive/Documents/Work/质谱分析/data")


def test_old_file_resolution():
    file = ThermoFile(DATA_PATH / "NOISE_ZERO" /
                      "11112019_morning_ambient.RAW")
    assert file.massResolution == 140000.


def test_new_type_file_resolution():
    file = ThermoFile(DATA_PATH / "221007 cali-full-range.raw")
    assert file.massResolution == 120000.
