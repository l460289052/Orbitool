# python

python 3.8

# packages

- h5py
- cython
- numpy # -c conda-forge with openblas
- scipy # -c conda-forge for numpy
- pandas
- matplotlib # will install qt
- pyteomics # -c bioconda
- sortedcontainers
- pythonnet # -c conda-forge
- pyinstaller # -c conda-forge

# env for debug

- pyside2 contains qt-designer, which was removed from pyqt5-tools, please install to another env
- pytest-qt to run qt app in a test




# if use pip

PyQt5 # if use pip

# if use conda

instruction to install openblas

```bash
conda install conda-forge::blas=*=openblas
conda install -c conda-forge numpy
```