import pickle
import re

replaces = {
    'Oribit': 'Orbit'
}

maps = {
    '_OrbitoolFormula': 'utils.formula._formula',
    '_OrbitoolElement': 'utils.formula._element',
    '_OrbitoolFormulaCalc': 'utils.formula._formulaCalc' }

def process(pattern):
    return r'(\W|^)'+pattern+r'(\W|$)'

maps = {process(k): v for k,v in maps.items()}

class Unpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str):
        for r, e in replaces.items():
            if r in module or r in name:
                module = module.replace(r, e)
                name = name.replace(r, e)

        for r, e in maps.items():
            if re.search(r, module) is not None:
                module = e

        return super().find_class(module, name)
