from Orbitool.structures import HDF5
from Orbitool.structures.HDF5 import datatable

def test_datatable():
    class files(datatable.Datatable):
        h5_type = HDF5.RegisterType('files')
        
        path = datatable.str_utf8()
        startDatetime = datatable.Datatime64s()
        endDatatime = datatable.Datatime64s()
        append = datatable.str_ascii_limit(length = 10)
        
        

    for file in files:
        print(file.path)
        
    files['path']
    files['startDatetime']
