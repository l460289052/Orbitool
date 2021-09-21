from dataclasses import dataclass
from array import array, ArrayType
from ...base import BaseStructure, field
from ...HDF5 import H5File
from ..h5type_handlers import Array


@dataclass
class SomeArray(BaseStructure):
    h5_type = "test some array"
    array_a: Array[int] = field(lambda: array("i"))
    array_b: Array['b'] = field(lambda: array("b"))
    array_c: Array[float] = field(lambda: array("d"))


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
