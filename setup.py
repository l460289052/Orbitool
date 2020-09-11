from distutils.core import setup
from Cython.Build import cythonize
import numpy as np
import os
import re
from typing import Dict

from utils.files import FolderTraveler

roots = ["utils", "functions"]
ft = FolderTraveler(roots, '.pyx', True)

def getModelName(path: str):
    name = os.path.split(path)[1]
    return os.path.splitext(name)[0]

class Node:
    def __init__(self, path):
        self.path = path
        self.ref = set()
        self.refed = set()

modelNodes: Dict[str, Node]= {}

for path in ft:
    node = Node(path)
    modelNodes[getModelName(path)] = node

def variableIn(variable: str, text: str):
    pattern = r'(\W|^)'+variable+r'(\W|$)'

    for piece in re.finditer(r'[^\n]*import[^\n]*', text):
        piece: re.match
        if re.search(pattern, piece.group()) is not None:
            return True
    return False

for model1, node1 in modelNodes.items():
    with open(node1.path, 'r') as f:
        text = f.read()
        for model2, node2 in modelNodes.items():
            if variableIn(model2, text):
                node1.ref.add(model2)
                node2.refed.add(model1)
                
                
def cythonSetup(filepath):
    cy = cythonize(filepath, annotate=True)
    setup(ext_modules=cy, script_args=['build_ext'], include_dirs=[
          np.get_include()], options={'build_ext': {'inplace': True}})


while len(modelNodes) > 0:
    processed = []

    for model1, node1 in modelNodes.items():
        if len(node1.ref) == 0:
            cythonSetup(node1.path)
            processed.append(model1)

            for model2 in node1.refed:
                node2 = modelNodes[model2]
                node2.ref.remove(model1)

    if len(processed) == 0:
        raise Exception("Loop", modelNodes.keys())
    for pro in processed:
        modelNodes.pop(pro)
