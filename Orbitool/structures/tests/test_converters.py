from ..h5converters import RestrictedCalc, ForceCalc, RestrictedCalcConverter, ForceCalcConverter
from ..HDF5 import H5File


def test_restricted():
    f = H5File()
    calc = RestrictedCalc()
    RestrictedCalcConverter.write_to_h5(f._obj, "calc", calc)
    calc = RestrictedCalcConverter.read_from_h5(f._obj, "calc")


def test_force():
    f = H5File()
    calc = ForceCalc()
    ForceCalcConverter.write_to_h5(f._obj, "calc", calc)
    calc = ForceCalcConverter.read_from_h5(f._obj, "calc")
