from Orbitool.structures import HDF5
import h5py
import io
import numpy as np

def test_lightlist():
    f = h5py.File(io.BytesIO(),'w')

    l:HDF5.LightList=HDF5.LightList.create_at(f,'l')
    l.initialize()
    for i in range(10):
        l.append([i]*10)
    
    r=HDF5.infer_from(f['l'])
    for i,item in enumerate(r):
        assert np.array_equal([i]*10,item)

