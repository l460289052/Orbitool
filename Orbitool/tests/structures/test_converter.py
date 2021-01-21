import pytest
import h5py
import io
from Orbitool.structures.converters import register, convert, _BaseConverter, ConvertVersionCheckError, _clear


@pytest.fixture
def h5file():
    f = h5py.File(io.BytesIO())
    f.attrs['version'] = '2'
    _clear()
    return f


def test_two_chain(h5file):
    class c1(_BaseConverter):
        version_to = "2"
        version_from = "1"

    class c2(_BaseConverter):
        version_to = "3"
        version_from = "2"

    class c3(_BaseConverter):
        version_to = "5"
        version_from = "4"

    class c4(_BaseConverter):
        version_to = "6"
        version_from = "5"

    list(map(register, [c1, c2, c3, c4]))

    with pytest.raises(ConvertVersionCheckError):
        convert(h5file)

    class c5(_BaseConverter):
        version_to = "4"
        version_from = "3"
    register(c5)
    convert(h5file)


def test_chain_convert(h5file):
    queue = []

    class c2(_BaseConverter):
        version_to = "3"
        version_from = "2"

        def convert(self, h5file) -> None:
            super().convert(h5file)
            queue.append(2)

    class c1(_BaseConverter):
        version_to = "2"
        version_from = "1"

        def convert(self, h5file) -> None:
            super().convert(h5file)
            queue.append(1)

    class c3(_BaseConverter):
        version_to = "4"
        version_from = "3"

        def convert(self, h5file) -> None:
            super().convert(h5file)
            queue.append(3)

    list(map(register, [c1, c2, c3]))

    convert(h5file)
    assert queue == [2, 3]
