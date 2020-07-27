from distutils.core import setup
from Cython.Build import cythonize
import numpy as np

cythonizes = [
cythonize("_OrbitoolElement.pyx", annotate=True),
cythonize("_OrbitoolFormula.pyx", annotate=True),
cythonize("_OrbitoolFormulaCalc.pyx", annotate=True),
cythonize("_OrbitoolFunc.pyx", annotate=True)
]
for cy in cythonizes:
    setup(ext_modules=cy, script_args=['build_ext'], include_dirs=[np.get_include()], options={'build_ext':{'inplace':True}})

import os
import shutil
for path in os.listdir('code'):
    if os.path.splitext(path)[1] == '.pyd':
        _path=os.path.join('code',path)
        if os.path.exists(path):
            if os.path.getmtime(_path) > os.path.getmtime(path):
                shutil.copyfile(_path,path)
        else:
            shutil.copyfile(_path,path)


from utils.files import FolderTraveler

roots = ["utils", "functions"]
ft = FolderTraveler(roots, '.pyx', True)
for filepath in ft:
    cy = cythonize(filepath, annotate=True)
    setup(ext_modules=cy, script_args=['build_ext'], include_dirs=[
          np.get_include()], options={'build_ext': {'inplace': True}})
