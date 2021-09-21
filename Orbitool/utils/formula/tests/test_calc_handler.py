from ..h5handlers import *
from ....structures.HDF5 import H5File


def test_restricted():
    f = H5File()
    calc = RestrictedCalc()
    handler = RestrictedCalcHandler()
    handler.write_to_h5(f._obj, "calc", calc)
    calc = handler.read_from_h5(f._obj, "calc")


def test_force():
    f = H5File()
    calc = ForceCalc()
    handler = ForceCalcHandler()
    handler.write_to_h5(f._obj, "calc", calc)
    calc = handler.read_from_h5(f._obj, "calc")
