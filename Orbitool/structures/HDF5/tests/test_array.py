from array import array, ArrayType
from ...base import BaseStructure
from ...HDF5 import H5File


class SomeArray(BaseStructure):
    h5_type = "test some array"
    array_a = array("i")
    array_b: ArrayType = array("b")
    array_c = array("d")


def test_array():
    f = H5File()

    sa = SomeArray()
    sa.array_a.extend(range(10))
    sa.array_b.extend(range(10))
    sa.array_c.extend(range(10))

    f.write("array", sa)

    sa: SomeArray = f.read("array")
    assert sa.array_a == array("i", range(10))
    assert sa.array_b == array("b", range(10))
    assert sa.array_c == array("d", range(10))
