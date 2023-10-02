from ..normal_distribution import NormalDistributionFunc
from .....models.spectrum.spectrum import Peak
import pandas as pd
import pathlib

root = pathlib.Path(__file__).parent


def test_split():
    func = NormalDistributionFunc(2.852197450904393e-06, 148889.02590153966)
    data = pd.read_csv(root.joinpath("peak_1.csv"))
    peak = Peak(data["mz"], data["intensity"])
    peaks = func.splitPeak(peak)
