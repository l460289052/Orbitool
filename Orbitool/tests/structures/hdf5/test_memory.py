import pytest
import io

from Orbitool.structures import HDF5
from . import some_descriptor_group

@pytest.fixture
def location():
    return HDF5.memory_h5_location.Location()

def test_group(location):
    some_descriptor_group.test_group(location)

def test_list(location):
    some_descriptor_group.test_group(location)

def test_dict(location):
    some_descriptor_group.test_dict(location)

def test_group_descriptor(location):
    some_descriptor_group.test_group_descriptor(location)