
from typing import Dict, List
import numpy as np
from Orbitool.base.h5file import H5File
from Orbitool.models.spectrum.peak import Peak


def test_write_list():
    seed = 1233
    np.random.seed(seed)
    a = [Peak(
        mz=np.random.rand(10),
        intensity=np.random.rand(10)
    ) for _ in range(10)]

    f = H5File()

    f.write("l", a, List[Peak])

    obj = f._obj
    assert len(obj["l"]["spectrum"]) == 100
    assert len(obj["l"]["peaks"]) == 10

    b = f.read("l", List[Peak])
    assert a == b


def test_write_dict():
    seed = 1233
    np.random.seed(seed)
    a = {str(i): Peak(
        mz=np.random.rand(10),
        intensity=np.random.rand(10)
    ) for i in range(10)}

    f = H5File()

    f.write("d", a, Dict[str, Peak])

    obj = f._obj
    assert len(obj["d"]["spectrum"]) == 100
    assert len(obj["d"]["peaks"]) == 10

    b = f.read("d", Dict[str, Peak])
    assert a == b
