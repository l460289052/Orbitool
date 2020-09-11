import pickle

class Unpickler(pickle.Unpickler):
    def find_class(self, module:str, name:str):
        if 'Oribit' in module or 'Oribit' in name:
            module=module.replace('Oribit','Orbit')
            name=name.replace('Oribit','Orbit')
        return super().find_class(module,name)

