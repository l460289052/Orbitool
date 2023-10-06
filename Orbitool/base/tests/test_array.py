from array import array

from pydantic import Field, TypeAdapter
import pytest

from .. import Array, BaseStructure, H5File
from ..structure import AnnotationError


def test_validate():
    with pytest.raises(AnnotationError) :
        ta = TypeAdapter(Array)
    ta = TypeAdapter(Array['i'])
    assert ta.validate_python(array('i', [1, 2, 3])) == array('i', [1, 2, 3])
    assert ta.validate_python([1, 2, 3]) == array('i', [1, 2, 3])
    with pytest.raises(TypeError):
        assert ta.validate_python("123") == array('i', [1, 2, 3])


def test_array():
    class SomeArray(BaseStructure):
        array_a: Array['i'] = array("i")
        array_b: Array['b'] = array("b")
        array_c: Array['f'] = array("d")

    f = H5File()

    sa = SomeArray()
    sa.array_a.extend(range(10))
    sa.array_b.extend(range(10))
    sa.array_c.extend(range(10))

    f.write("array", sa)

    sa: SomeArray = f.read("array", SomeArray)
    assert sa.array_a == array("i", range(10))
    assert sa.array_b == array("b", range(10))
    assert sa.array_c == array("d", range(10))
