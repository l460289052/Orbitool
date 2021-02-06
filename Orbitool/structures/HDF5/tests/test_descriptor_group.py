import pytest
from h5py import File
import io

from Orbitool.structures import HDF5
from . import some_descriptor_group

def test_subclass_type():
    with pytest.raises(AssertionError):
        class Spectrum(HDF5.Group):
            pass

@pytest.fixture
def h5file():
    return File(io.BytesIO(), 'w')

def test_group(h5file):
    some_descriptor_group.test_group(h5file)

def test_list(h5file):
    some_descriptor_group.test_group(h5file)

def test_dict(h5file):
    some_descriptor_group.test_dict(h5file)

def test_group_descriptor(h5file):
    some_descriptor_group.test_group_descriptor(h5file)

def test_ref_attr(h5file):
    some_descriptor_group.test_ref_attr(h5file)
