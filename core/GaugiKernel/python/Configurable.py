__all__ = ["Configurable"]

import ROOT
from GaugiKernel import Logger
from GaugiKernel.Cpp import treatPropertyValue
from GaugiKernel.macros import MSG_FATAL

class Configurable(Logger):
    _subclasses = {}

    def __init__(self, core_class, *args, **kwargs):
        Logger.__init__(self)
        self._core = core_class(*args)
        
        properties = [str(p) for p in self._core.getProperties()] if hasattr(self._core, "getProperties") else []
        
        # Initialize properties in __dict__ to None by default
        for prop in properties:
            self.__dict__[prop] = None

        if self.__class__ is Configurable:
            class_name = f"Configurable_{core_class.__name__}"
            if class_name not in Configurable._subclasses:
                dct = {}
                
                for prop in properties:
                    # Closure helper to avoid late binding issues
                    def make_funcs(p):
                        def fget(self):
                            return self.__dict__.get(p)
                        def fset(self, val):
                            self.setProperty(p, val)
                        return fget, fset
                    
                    fget, fset = make_funcs(prop)
                    dct[prop] = property(fget, fset)
                    
                    # camelCase methods
                    cap_prop = prop[0].upper() + prop[1:] if prop else prop
                    dct[f"get{cap_prop}"] = lambda self, p=prop: self.getProperty(p)
                    dct[f"set{cap_prop}"] = lambda self, val, p=prop: self.setProperty(p, val)
                    
                    # snake_case methods
                    dct[f"get_{prop}"] = lambda self, p=prop: self.getProperty(p)
                    dct[f"set_{prop}"] = lambda self, val, p=prop: self.setProperty(p, val)
                
                subcls = type(class_name, (Configurable,), dct)
                Configurable._subclasses[class_name] = subcls
            
            self.__class__ = Configurable._subclasses[class_name]

        # Apply keyword arguments
        for key, val in kwargs.items():
            self.setProperty(key, val)

    def __del__(self):
        del self._core

    def core(self):
        return self._core

    def setProperty(self, key, value):
        if self._core.hasProperty(key):
            self.__dict__[key] = value
            try:
                self._core.setProperty(key, treatPropertyValue(value))
            except Exception as e:
                MSG_FATAL(self, f"Exception in property with name {key} and value: {value}. Error: {e}")
        else:
            MSG_FATAL(self, f"Property with name {key} is not allowed for this object")

    def getProperty(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            MSG_FATAL(self, "Property with name %s is not allowed for %s object", key, self.__class__.__name__)
