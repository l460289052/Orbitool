from h5py import Group as H5Group

from ..structure import (
    AnnotationError, AttrTypeHandler, BaseStructure,
    DatasetTypeHandler, GroupTypeHandler)

H5_DT_ARGS = {
    "compression": "gzip",
    "compression_opts": 1
}
